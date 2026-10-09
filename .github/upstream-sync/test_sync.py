import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('sync.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        previous = Path.cwd()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'fork'
        self.repo.mkdir()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, previous)
        self.env = patch.dict(os.environ, {
            'GITHUB_REPOSITORY': 'ExampleOwner/sub2api',
            'UPSTREAM_REPOSITORY': 'Wei-Shaw/sub2api',
            'SYNC_BRANCH': 'main', 'REQUESTED_TAG': '', 'REQUESTED_REVISION': '', 'MANUAL_SYNC': 'false',
            'SYNC_REPORT': str(self.root / 'report.json'),
            'GITHUB_OUTPUT': str(self.root / 'output'),
            'GITHUB_STEP_SUMMARY': str(self.root / 'summary'),
            'GITHUB_RUN_ID': '123', 'NOTIFY_USERS': 'ExampleOwner',
            'TELEGRAM_BOT_TOKEN': '', 'TELEGRAM_CHAT_ID': '',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        sync.git('init', '-b', 'main')
        sync.configure_git()
        Path('frontend').mkdir()
        Path('frontend/brand').write_text('Sub2API\n')
        Path('backend/cmd/server').mkdir(parents=True)
        Path('backend/cmd/server/VERSION').write_text('1.0.0\n')
        for path in sync.FORK_READMES:
            Path(path).write_text('Original project documentation\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'base')
        self.base = sync.git('rev-parse', 'HEAD').stdout.strip()
        self.release = {'id': 42, 'tag_name': 'v1.1.0', 'draft': False,
                        'prerelease': False, 'published_at': '2026-10-01T00:00:00Z',
                        'html_url': 'https://github.com/Wei-Shaw/sub2api/releases/tag/v1.1.0',
                        'body': 'An upstream release'}
        self.origin = self.root / 'origin.git'
        sync.git('init', '--bare', str(self.origin))
        sync.git('remote', 'add', 'origin', str(self.origin))
        self.api = Mock(repository='ExampleOwner/sub2api')
        self.api.alert.return_value = None
        self.api.release.side_effect = lambda tag='', upstream=False: self.release if upstream else None

    def histories(self, conflict=False, readme_conflict=False):
        sync.git('checkout', '-b', 'upstream')
        Path('backend/new-feature').write_text('new upstream behavior\n')
        if conflict:
            Path('frontend/brand').write_text('upstream replacement\n')
        if readme_conflict:
            for path in sync.FORK_READMES:
                Path(path).write_text('Updated upstream documentation\n')
            Path('backend/cmd/server/VERSION').write_text('1.1.0\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'upstream update')
        upstream_sha = sync.git('rev-parse', 'HEAD').stdout.strip()
        sync.git('tag', self.release['tag_name'])
        sync.git('checkout', 'main')
        Path('frontend/brand').write_text('BNDS AI普及计划\n')
        if readme_conflict:
            for path in sync.FORK_READMES:
                Path(path).write_text('BNDS fork documentation\n')
            Path('backend/cmd/server/VERSION').write_text('1.0.0-1\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'custom frontend')
        fork_sha = sync.git('rev-parse', 'HEAD').stdout.strip()
        return upstream_sha, fork_sha

    def test_merge_keeps_fork_frontend_and_new_upstream_code(self):
        upstream_sha, fork_sha = self.histories()
        sync.git('tag', '-d', 'v1.1.0')  # Only the upstream remote owns this tag initially.
        result = sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertNotEqual(result, upstream_sha)
        self.assertNotEqual(result, fork_sha)
        self.assertEqual(Path('frontend/brand').read_text(), 'BNDS AI普及计划\n')
        self.assertTrue(Path('backend/new-feature').exists())
        self.assertEqual(Path('backend/cmd/server/VERSION').read_text(), '1.1.0-1\n')
        self.assertEqual(sync.git('rev-parse', 'v1.1.0-1^{commit}').stdout.strip(), result)
        self.assertIn(upstream_sha, sync.git('show', '-s', '--format=%P', 'HEAD').stdout)
        self.assertFalse(sync.read_state()['published'])
        sync.git('push', '--atomic', 'origin', 'HEAD:refs/heads/main', 'refs/tags/v1.1.0-1:refs/tags/v1.1.0-1')
        remote = sync.git('ls-remote', 'origin', 'refs/tags/v1.1.0-1^{}').stdout
        self.assertIn(result, remote)

    def test_conflict_aborts_without_replacing_frontend_or_creating_fork_tag(self):
        upstream_sha, fork_sha = self.histories(conflict=True)
        sync.git('tag', '-d', 'v1.1.0')
        with self.assertRaisesRegex(RuntimeError, 'merge conflict'):
            sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertEqual(sync.git('rev-parse', 'HEAD').stdout.strip(), fork_sha)
        self.assertEqual(Path('frontend/brand').read_text(), 'BNDS AI普及计划\n')
        self.assertFalse(sync.STATE.exists())
        self.assertNotEqual(sync.git('rev-parse', '--verify', 'refs/tags/v1.1.0-1', check=False).returncode, 0)
        self.assertEqual(json.loads(Path(os.environ['SYNC_REPORT']).read_text())['conflicts'], ['frontend/brand'])
        self.assertEqual(sync.git('status', '--porcelain').stdout, '')

    def test_readme_and_version_conflicts_do_not_block_upstream_code(self):
        upstream_sha, _ = self.histories(readme_conflict=True)
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        for path in sync.FORK_READMES:
            self.assertEqual(Path(path).read_text(), 'BNDS fork documentation\n')
        self.assertTrue(Path('backend/new-feature').exists())
        self.assertEqual(Path('backend/cmd/server/VERSION').read_text(), '1.1.0-1\n')
        self.assertEqual(sync.git('diff', '--name-only', '--diff-filter=U').stdout, '')
        self.assertIn(upstream_sha, sync.git('show', '-s', '--format=%P', 'HEAD').stdout)

    def test_clean_upstream_readme_edits_and_deletions_keep_fork_files(self):
        sync.git('checkout', '-b', 'upstream')
        Path('README.md').write_text('Upstream-only edit\n')
        sync.git('rm', 'README_CN.md')
        Path('backend/new-feature').write_text('new upstream behavior\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'upstream documentation and code')
        upstream_sha = sync.git('rev-parse', 'HEAD').stdout.strip()
        sync.git('checkout', 'main')
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        for path in sync.FORK_READMES:
            self.assertEqual(Path(path).read_text(), 'Original project documentation\n')
        self.assertTrue(Path('backend/new-feature').exists())

    def test_upstream_readme_updates_do_not_restore_deleted_fork_readmes(self):
        sync.git('checkout', '-b', 'upstream')
        Path('README_JA.md').write_text('Updated upstream Japanese documentation\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'upstream documentation')
        upstream_sha = sync.git('rev-parse', 'HEAD').stdout.strip()
        sync.git('checkout', 'main')
        sync.git('rm', 'README_JA.md')
        sync.git('commit', '-m', 'remove unused fork documentation')
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertFalse(Path('README_JA.md').exists())
        self.assertNotIn('README_JA.md', sync.git('ls-files').stdout)

    def test_readme_policy_still_aborts_and_reports_code_conflicts(self):
        upstream_sha, fork_sha = self.histories(conflict=True, readme_conflict=True)
        with self.assertRaisesRegex(RuntimeError, 'merge conflict'):
            sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertEqual(sync.git('rev-parse', 'HEAD').stdout.strip(), fork_sha)
        self.assertEqual(json.loads(Path(os.environ['SYNC_REPORT']).read_text())['conflicts'], ['frontend/brand'])
        for path in sync.FORK_READMES:
            self.assertEqual(Path(path).read_text(), 'BNDS fork documentation\n')
        self.assertEqual(sync.git('status', '--porcelain').stdout, '')

    def test_full_sync_pushes_the_custom_tag_and_outputs_release_input(self):
        upstream_sha, _ = self.histories()
        upstream_repo = self.root / 'upstream.git'
        sync.git('clone', '--bare', '.', str(upstream_repo))
        sync.git('tag', '-d', 'v1.1.0')
        original_git = sync.git

        def local_fetch(*args, **kwargs):
            if args[0] == 'fetch':
                self.assertIn('refs/upstream-release/v1.1.0', args[-1])
                args = (*args[:2], str(upstream_repo), *args[3:])
            return original_git(*args, **kwargs)

        with patch.object(sync, 'git', side_effect=local_fetch):
            sync.sync(self.api)
        fork_sha = sync.git('rev-parse', 'v1.1.0-1^{commit}').stdout.strip()
        self.assertNotEqual(fork_sha, upstream_sha)
        self.assertEqual(Path('frontend/brand').read_text(), 'BNDS AI普及计划\n')
        self.assertIn(fork_sha, sync.git('ls-remote', 'origin', 'refs/heads/main').stdout)
        self.assertIn(fork_sha, sync.git('ls-remote', 'origin', 'refs/tags/v1.1.0-1^{}').stdout)
        outputs = Path(os.environ['GITHUB_OUTPUT']).read_text()
        self.assertIn('ready=true', outputs)
        self.assertIn('tag=v1.1.0-1', outputs)

    def test_existing_upstream_tag_is_not_published_or_force_replaced(self):
        upstream_sha, _ = self.histories()
        sync.git('tag', 'v1.1.0-1', upstream_sha)
        with self.assertRaisesRegex(RuntimeError, 'refusing to replace'):
            sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertEqual(sync.git('rev-parse', 'v1.1.0-1^{commit}').stdout.strip(), upstream_sha)

    def test_retry_reuses_exact_customized_commit(self):
        upstream_sha, _ = self.histories()
        sync.git('tag', '-d', 'v1.1.0')
        first = sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertEqual(sync.prepare_tag('v1.1.0-1', upstream_sha, self.release), first)
        self.assertEqual(sync.git('rev-parse', 'HEAD').stdout.strip(), first)

    def test_pending_tag_from_another_branch_is_refused(self):
        upstream_sha, fork_sha = self.histories()
        sync.git('tag', '-d', 'v1.1.0')
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        sync.git('checkout', '--detach', fork_sha)
        with self.assertRaisesRegex(RuntimeError, 'not an ancestor'):
            sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)

    def test_open_alert_pauses_scheduled_runs(self):
        self.api.alert.return_value = {'html_url': 'https://github.com/example/issues/1'}
        sync.sync(self.api)
        self.api.release.assert_not_called()
        self.assertIn('ready=false', Path(os.environ['GITHUB_OUTPUT']).read_text())

    def test_manual_run_can_retry_after_alert(self):
        os.environ['MANUAL_SYNC'] = 'true'
        self.api.alert.return_value = {'html_url': 'https://github.com/example/issues/1'}
        self.api.release.return_value = None
        self.api.release.side_effect = None
        sync.sync(self.api)
        self.api.release.assert_called_once_with('', upstream=True)

    def test_successfully_published_version_is_not_rebuilt(self):
        sync.write_state({**self.release, 'tag': 'v1.1.0-1', 'upstream_tag': 'v1.1.0', 'revision': 1, 'release_id': 42, 'published': True})
        sync.sync(self.api)
        self.api.release.assert_called_once_with('', upstream=True)
        self.assertNotIn('ready=true', Path(os.environ['GITHUB_OUTPUT']).read_text())

    def test_new_upstream_starts_at_one_and_manual_next_increments_numerically(self):
        state = {'upstream_tag': 'v1.1.0', 'tag': 'v1.1.0-2', 'revision': 2,
                 'release_id': 42, 'published': True}
        self.assertIsNone(sync.select_tag('v1.1.0', self.release, state, ''))
        sync.git('tag', 'v1.1.0-10')
        self.assertEqual(sync.select_tag('v1.1.0', self.release, state, 'next'), 'v1.1.0-11')
        newer = {**self.release, 'id': 43, 'tag_name': 'v1.2.0'}
        self.assertEqual(sync.select_tag('v1.2.0', newer, state, ''), 'v1.2.0-1')
        for revision in ('0', '-1', '01', '1.2', 'bad'):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                sync.select_tag('v1.1.0', self.release, state, revision)

    def test_pending_revision_is_retried_without_incrementing(self):
        state = {'upstream_tag': 'v1.1.0', 'tag': 'v1.1.0-2', 'revision': 2,
                 'release_id': 42, 'published': False}
        for revision in ('', 'next', '2'):
            self.assertEqual(sync.select_tag('v1.1.0', self.release, state, revision), 'v1.1.0-2')
        with self.assertRaisesRegex(ValueError, 'pending revision'):
            sync.select_tag('v1.1.0', self.release, state, '3')

    def test_second_revision_includes_new_frontend_and_preserves_source_tag(self):
        upstream_sha, _ = self.histories()
        first = sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        state = sync.read_state()
        state['published'] = True
        sync.write_state(state)
        Path('frontend/brand').write_text('BNDS frontend revision 2\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'frontend improvements')
        tag = sync.select_tag('v1.1.0', self.release, state, 'next')
        second = sync.prepare_tag(tag, upstream_sha, self.release)
        self.assertEqual(tag, 'v1.1.0-2')
        self.assertNotEqual(first, second)
        self.assertEqual(sync.git('rev-parse', 'v1.1.0^{commit}').stdout.strip(), upstream_sha)
        self.assertEqual(Path('frontend/brand').read_text(), 'BNDS frontend revision 2\n')
        self.assertEqual(Path('backend/cmd/server/VERSION').read_text(), '1.1.0-2\n')
        self.assertEqual(sync.read_state()['upstream_tag'], 'v1.1.0')
        self.assertEqual(sync.read_state()['revision'], 2)

    def test_version_metadata_conflict_is_regenerated_from_fork_tag(self):
        sync.git('checkout', '-b', 'upstream')
        Path('backend/cmd/server/VERSION').write_text('1.1.0\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'upstream version')
        upstream_sha = sync.git('rev-parse', 'HEAD').stdout.strip()
        sync.git('checkout', 'main')
        Path('backend/cmd/server/VERSION').write_text('1.0.0-1\n')
        sync.git('add', '.')
        sync.git('commit', '-m', 'fork version')
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        self.assertEqual(Path('backend/cmd/server/VERSION').read_text(), '1.1.0-1\n')
        self.assertEqual(sync.git('diff', '--name-only', '--diff-filter=U').stdout, '')

    def test_existing_fork_release_is_not_overwritten(self):
        self.api.release.side_effect = lambda tag='', upstream=False: self.release
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            sync.sync(self.api)

    def test_older_release_cannot_roll_back_default_branch(self):
        sync.write_state({'tag': 'v1.2.0', 'published_at': '2026-10-02T00:00:00Z', 'published': True})
        with self.assertRaisesRegex(ValueError, 'older release'):
            sync.sync(self.api)

    def test_invalid_input_and_draft_release_are_refused(self):
        os.environ['REQUESTED_TAG'] = 'v1.1.0\nmalicious'
        with self.assertRaisesRegex(ValueError, 'version tag'):
            sync.sync(self.api)
        os.environ['REQUESTED_TAG'] = 'v1.1.0'
        self.release['draft'] = True
        with self.assertRaisesRegex(ValueError, 'published version'):
            sync.sync(self.api)

    def test_finish_records_only_verified_publication_and_closes_alert(self):
        upstream_sha, _ = self.histories()
        sync.git('tag', '-d', 'v1.1.0')
        sync.prepare_tag('v1.1.0-1', upstream_sha, self.release)
        sync.git('push', 'origin', 'HEAD:refs/heads/main')
        os.environ['REQUESTED_TAG'] = 'v1.1.0-1'
        self.api.release.side_effect = None
        self.api.release.return_value = self.release
        self.api.alert.return_value = {'number': 1}
        sync.finish(self.api)
        self.assertTrue(sync.read_state()['published'])
        self.assertEqual(self.api.request.call_args.args[-1], {'state': 'closed'})

    def test_finish_rejects_absent_or_draft_release(self):
        os.environ['REQUESTED_TAG'] = 'v1.1.0-1'
        sync.write_state({'tag': 'v1.1.0-1', 'published': False})
        with self.assertRaisesRegex(RuntimeError, 'matching published release'):
            sync.finish(self.api)
        self.assertFalse(sync.read_state()['published'])

    def test_conflict_notification_mentions_owner_and_updates_single_issue(self):
        sync.report(tag='v1.1.0', conflicts=['frontend/brand'])
        self.api.request.return_value = {'html_url': 'https://github.com/example/issues/1'}
        sync.notify(self.api)
        method, path, payload = self.api.request.call_args.args
        self.assertEqual(method, 'POST')
        self.assertTrue(path.endswith('/issues'))
        self.assertIn('@ExampleOwner', payload['body'])
        self.assertIn('`frontend/brand`', payload['body'])
        self.assertIn('/actions/runs/123', payload['body'])
        self.api.alert.return_value = {'number': 1}
        sync.notify(self.api)
        self.assertEqual(self.api.request.call_args.args[0], 'PATCH')

    def test_workflow_permission_notification_explains_failure_and_token_fix(self):
        for permission in ('workflows', 'workflow'):
            with self.subTest(permission=permission):
                error = ("git push failed: refusing to update workflow `.github/workflows/backend-ci.yml` "
                         f"without `{permission}` " + ('permission' if permission == 'workflows' else 'scope'))
                sync.report(tag='v1.1.0-1', error=error)
                self.api.request.return_value = {'html_url': 'https://github.com/example/issues/1'}
                sync.notify(self.api)
                body = self.api.request.call_args.args[-1]['body']
                self.assertIn(error, body)
                self.assertIn('UPSTREAM_SYNC_TOKEN', body)
                self.assertIn('Contents 和 Workflows', body)
                self.assertNotIn('冲突文件：', body)

    def test_other_failure_notification_includes_reported_reason(self):
        sync.report(tag='v1.1.0-1', error='release tag is not an ancestor of the default branch')
        self.api.request.return_value = {'html_url': 'https://github.com/example/issues/1'}
        sync.notify(self.api)
        body = self.api.request.call_args.args[-1]['body']
        self.assertIn('release tag is not an ancestor of the default branch', body)
        self.assertNotIn('这是工作流写入权限不足', body)


if __name__ == '__main__':
    unittest.main()
