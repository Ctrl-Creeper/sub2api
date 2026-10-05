import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('release_matrix', Path(__file__).with_name('release_matrix.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseMatrixTest(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous)
        for name in ('.goreleaser.yaml', '.goreleaser.simple.yaml'):
            shutil.copyfile(ROOT / name, name)
        Path('backend/cmd/server').mkdir(parents=True)
        release.VERSION_FILE.write_text('9.8.7-1\n')

    def fixture_artifacts(self, simple=False):
        directory = Path('release-input')
        directory.mkdir()
        for target in release.targets(simple):
            name = release.archive_name('9.8.7-1', target)
            archive = directory / name
            if target['goos'] == 'linux':
                with tarfile.open(archive, 'w:gz') as out:
                    info = tarfile.TarInfo('sub2api')
                    info.size = 7
                    info.mode = 0o755
                    out.addfile(info, io.BytesIO(b'fixture'))
            else:
                archive.write_bytes(b'fixture archive')
            metadata = {'version': '9.8.7-1', 'sha': 'a' * 40, 'target': target,
                        'archive': name, 'sha256': release.sha256(archive)}
            (directory / f"manifest-{target['goos']}-{target['goarch']}.json").write_text(json.dumps(metadata))
        return argparse.Namespace(input='release-input', version='9.8.7-1', sha='a' * 40, simple=simple, output='contexts')

    def test_full_and_simple_matrix_match_existing_targets(self):
        full = release.targets()
        self.assertEqual(len(full), 5)
        self.assertNotIn({'goos': 'windows', 'goarch': 'arm64'}, full)
        self.assertEqual(release.targets(True), [{'goos': 'linux', 'goarch': 'amd64'}])

    def test_leaf_keeps_packaging_and_selects_only_one_target(self):
        original = release.config()
        release.generate_config(argparse.Namespace(mode='build', simple=False, goos='darwin', goarch='arm64', output='leaf.yaml'))
        leaf = yaml.safe_load(Path('leaf.yaml').read_text())
        self.assertEqual(leaf['builds'][0]['goos'], ['darwin'])
        self.assertEqual(leaf['builds'][0]['goarch'], ['arm64'])
        self.assertEqual(leaf['builds'][0]['ignore'], [])
        self.assertEqual(leaf['archives'], original['archives'])
        self.assertEqual(leaf['release'], original['release'])
        self.assertFalse(leaf['dockers'])
        self.assertIn('{{ .Env.RELEASE_DATE }}', '\n'.join(leaf['builds'][0]['ldflags']))

    def test_publication_config_has_no_compilation_or_docker_work(self):
        for simple in (False, True):
            with self.subTest(simple=simple):
                original = release.config()
                release.generate_config(argparse.Namespace(mode='publish', simple=simple, output='publisher.yaml'))
                data = yaml.safe_load(Path('publisher.yaml').read_text())
                self.assertTrue(data['builds'][0]['skip'])
                self.assertFalse(data['archives'])
                self.assertFalse(data['dockers'])
                self.assertEqual(data['release']['header'], original['release']['header'])
                self.assertEqual(data['release']['footer'], original['release']['footer'])
                self.assertFalse(data['release'].get('skip_upload', False))
                self.assertEqual(data['checksum']['extra_files'], data['release']['extra_files'])
                self.assertEqual(data['release']['extra_files'], [
                    {'glob': 'release-input/' + release.archive_name('9.8.7-1', target)}
                    for target in release.targets(simple)
                ])

    def test_collect_and_verify_hash_and_source_binding(self):
        args = self.fixture_artifacts()
        release.verify(args)
        file = next(Path(args.input).glob('*.tar.gz'))
        file.write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            release.verify(args)

    def test_missing_extra_and_wrong_commit_artifacts_are_rejected(self):
        args = self.fixture_artifacts(True)
        args.sha = 'b' * 40
        with self.assertRaises(ValueError):
            release.verify(args)
        args.sha = 'a' * 40
        Path('release-input/unexpected').write_text('not an asset')
        with self.assertRaises(ValueError):
            release.verify(args)
        Path('release-input/unexpected').unlink()
        next(Path('release-input').glob('*.tar.gz')).unlink()
        with self.assertRaises(FileNotFoundError):
            release.verify(args)

    def test_linux_context_preserves_binary_executable_mode(self):
        args = self.fixture_artifacts()
        Path('Dockerfile.goreleaser').write_text('FROM scratch\nCOPY sub2api /sub2api\n')
        Path('deploy').mkdir()
        Path('deploy/docker-entrypoint.sh').write_text('#!/bin/sh\nexec /app/sub2api\n')
        Path('backend/resources').mkdir()
        Path('backend/resources/data').write_text('fixture')
        release.contexts(args)
        for arch in ('amd64', 'arm64'):
            binary = Path('contexts') / arch / 'sub2api'
            self.assertEqual(binary.read_bytes(), b'fixture')
            self.assertEqual(binary.stat().st_mode & 0o777, 0o755)

    def test_plan_requires_a_tag_for_publication(self):
        args = argparse.Namespace(ref='main', dry_run=False, simple=False)
        with patch.object(subprocess, 'check_output', return_value='a' * 40 + '\n'):
            with self.assertRaisesRegex(ValueError, 'fork version tag'):
                release.plan(args)
        args.ref = 'v9.8.7-1'
        with patch.object(subprocess, 'check_output', side_effect=['a' * 40 + '\n', 'b' * 40 + '\n']):
            with self.assertRaisesRegex(ValueError, 'does not match'):
                release.plan(args)

    def test_dry_run_plan_resolves_matrix_without_a_new_tag(self):
        with patch.dict(os.environ, {'GITHUB_OUTPUT': 'outputs', 'GITHUB_REPOSITORY_OWNER': 'ExampleOwner'}), patch.object(subprocess, 'check_output', return_value='a' * 40 + '\n'):
            release.plan(argparse.Namespace(ref='feature/matrix', dry_run=True, simple=False))
        output = dict(line.split('=', 1) for line in Path('outputs').read_text().splitlines())
        self.assertEqual(output['dry_run'], 'true')
        self.assertEqual(output['owner_lower'], 'exampleowner')
        self.assertEqual(len(json.loads(output['matrix'])['include']), 5)

    def test_upstream_tags_and_invalid_revisions_cannot_be_published(self):
        for tag in ('v9.8.7', 'v9.8.7-0', 'v9.8.7-01', 'v9.8.7-rc1'):
            with self.subTest(tag=tag), patch.object(subprocess, 'check_output', return_value='a' * 40):
                with self.assertRaisesRegex(ValueError, 'fork version tag'):
                    release.plan(argparse.Namespace(ref=tag, dry_run=False, simple=False))

    def test_source_build_uses_fork_tags_and_numeric_revision_order(self):
        scripts = Path('backend/scripts')
        scripts.mkdir()
        shutil.copyfile(ROOT / 'backend/scripts/resolve-version.sh', scripts / 'resolve-version.sh')
        subprocess.run(['git', 'init', '-q'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-qm', 'fixture'], check=True)

        def resolved():
            return subprocess.check_output(['sh', str(scripts / 'resolve-version.sh')], text=True).strip()

        self.assertEqual(resolved(), '9.8.7-1')
        subprocess.run(['git', 'tag', 'v9.8.7'], check=True)
        self.assertEqual(resolved(), '9.8.7-1')
        for tag in ('v9.8.7-2', 'v9.8.7-10'):
            subprocess.run(['git', 'tag', tag], check=True)
        self.assertEqual(resolved(), '9.8.7-10')

    def test_numeric_revision_is_stable_but_upstream_rc_is_prerelease(self):
        for version, prerelease in [('9.8.7-1', False), ('9.8.7-10', False), ('9.8.7-rc1-2', True)]:
            for simple in (False, True):
                with self.subTest(version=version, simple=simple), patch.dict(os.environ, {'RELEASE_VERSION': version}):
                    release.generate_config(argparse.Namespace(mode='publish', simple=simple, output='publisher.yaml'))
                    data = yaml.safe_load(Path('publisher.yaml').read_text())
                    self.assertEqual(data['release']['prerelease'], prerelease)
                    self.assertIn('BNDS AI普及计划', data['release']['name_template'])
                    self.assertTrue(data['release']['name_template'].startswith('v{{.Version}}'))
                    self.assertIn(version, release.archive_name(version, release.targets()[0]))

    def test_pat_tag_push_does_not_duplicate_managed_release(self):
        state = Path('.github/upstream-sync/state.json')
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({'tag': 'v9.8.7-1'}))
        with patch.dict(os.environ, {'GITHUB_OUTPUT': 'outputs'}), patch.object(subprocess, 'check_output') as git:
            release.plan(argparse.Namespace(ref='v9.8.7-1', event='push', dry_run=False, simple=False))
        git.assert_not_called()
        self.assertEqual(Path('outputs').read_text(), 'skip=true\n')

    def test_managed_tag_remains_available_for_explicit_manual_release(self):
        state = Path('.github/upstream-sync/state.json')
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({'tag': 'v9.8.7-1'}))
        with patch.dict(os.environ, {'GITHUB_OUTPUT': 'outputs'}), patch.object(subprocess, 'check_output', return_value='a' * 40 + '\n'):
            release.plan(argparse.Namespace(ref='v9.8.7-1', event='workflow_dispatch', dry_run=False, simple=False))
        self.assertIn('tag=v9.8.7-1\n', Path('outputs').read_text())
        self.assertNotIn('skip=true', Path('outputs').read_text())

    def test_docker_commands_do_not_publish_during_dry_run(self):
        fake_bin = Path('bin')
        fake_bin.mkdir()
        docker = fake_bin / 'docker'
        docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DOCKER_LOG"\n')
        docker.chmod(0o755)
        env = {**os.environ, 'PATH': str(fake_bin.resolve()) + os.pathsep + os.environ['PATH'],
               'DOCKER_LOG': str(Path('docker.log').resolve()), 'RUNNER_TEMP': self.temp.name,
               'RELEASE_VERSION': '9.8.7-1', 'RELEASE_SHA': 'a' * 40, 'GITHUB_REPOSITORY': 'ExampleOwner/sub2api',
               'DRY_RUN': 'true', 'SIMPLE_RELEASE': 'false', 'DOCKERHUB_USERNAME': 'skip'}
        subprocess.run(['bash', str(ROOT / '.github/release-tools/release-images.sh')], env=env, check=True)
        log = Path('docker.log').read_text()
        self.assertEqual(log.count('buildx build'), 2)
        self.assertIn('linux/arm64', log)
        self.assertNotIn('--push', log)
        self.assertNotIn('imagetools', log)
        self.assertNotIn('skip/sub2api', log)
        self.assertIn('ghcr.io/exampleowner/sub2api', log)


    def test_published_full_and_simple_image_tags(self):
        fake_bin = Path('bin')
        fake_bin.mkdir()
        docker = fake_bin / 'docker'
        docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DOCKER_LOG"\n')
        docker.chmod(0o755)
        for simple in (False, True):
            with self.subTest(simple=simple):
                log_path = Path(f'docker-{simple}.log').resolve()
                env = {**os.environ, 'PATH': str(fake_bin.resolve()) + os.pathsep + os.environ['PATH'],
                       'DOCKER_LOG': str(log_path), 'RUNNER_TEMP': self.temp.name,
                       'RELEASE_VERSION': '9.8.7-1', 'RELEASE_SHA': 'a' * 40, 'GITHUB_REPOSITORY': 'ExampleOwner/sub2api',
                       'DRY_RUN': 'false', 'SIMPLE_RELEASE': str(simple).lower(), 'DOCKERHUB_USERNAME': 'fixturehub'}
                subprocess.run(['bash', str(ROOT / '.github/release-tools/release-images.sh')], env=env, check=True)
                log = log_path.read_text()
                self.assertIn('--push', log)
                self.assertEqual(log.count('buildx build'), 1 if simple else 2)
                if simple:
                    self.assertNotIn('fixturehub', log)
                    self.assertNotIn('imagetools', log)
                    self.assertIn('ghcr.io/exampleowner/sub2api:latest', log)
                else:
                    self.assertEqual(log.count('imagetools create'), 2)
                    self.assertIn('fixturehub/sub2api:9.8', log)
                    self.assertIn('ghcr.io/exampleowner/sub2api:9', log)

    def test_upstream_prerelease_images_do_not_replace_latest(self):
        fake_bin = Path('bin')
        fake_bin.mkdir()
        docker = fake_bin / 'docker'
        docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DOCKER_LOG"\n')
        docker.chmod(0o755)
        for simple in (False, True):
            log_path = Path(f'rc-{simple}.log').resolve()
            env = {**os.environ, 'PATH': str(fake_bin.resolve()) + os.pathsep + os.environ['PATH'],
                   'DOCKER_LOG': str(log_path), 'RUNNER_TEMP': self.temp.name,
                   'RELEASE_VERSION': '9.8.7-rc1-1', 'RELEASE_SHA': 'a' * 40,
                   'GITHUB_REPOSITORY': 'ExampleOwner/sub2api', 'DOCKERHUB_USERNAME': 'skip',
                   'DRY_RUN': 'false', 'SIMPLE_RELEASE': str(simple).lower()}
            subprocess.run(['bash', str(ROOT / '.github/release-tools/release-images.sh')], env=env, check=True)
            log = log_path.read_text()
            self.assertIn('ghcr.io/exampleowner/sub2api:9.8.7-rc1-1', log)
            self.assertNotIn(':latest', log)
            self.assertNotIn('--tag ghcr.io/exampleowner/sub2api:9.8 ', log)



if __name__ == '__main__':
    unittest.main()
