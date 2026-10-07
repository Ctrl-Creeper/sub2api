#!/usr/bin/env python3
"""Merge published upstream releases without discarding fork modifications."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

STATE = Path('.github/upstream-sync/state.json')
ISSUE_MARKER = '<!-- bnds-upstream-release-sync -->'
TAG_RE = re.compile(r'v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?')
FORK_TAG_RE = re.compile(r'v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?-[1-9]\d*')
REPO_RE = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')
FORK_READMES = ('README.md', 'README_CN.md', 'README_JA.md')


class GitHub:
    def __init__(self, repository):
        if not REPO_RE.fullmatch(repository):
            raise ValueError('invalid GitHub repository')
        self.repository = repository

    def request(self, method, path, data=None, missing_ok=False):
        payload = None if data is None else json.dumps(data).encode()
        request = Request('https://api.github.com' + path, data=payload, method=method,
                          headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                                   'Accept': 'application/vnd.github+json',
                                   'Content-Type': 'application/json',
                                   'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            if missing_ok and error.code == 404:
                return None
            # Do not include response/request headers or tokens in CI logs.
            raise RuntimeError(f'GitHub API {method} {path}: HTTP {error.code}') from None

    def release(self, tag='', upstream=False):
        repository = os.environ['UPSTREAM_REPOSITORY'] if upstream else self.repository
        if not REPO_RE.fullmatch(repository):
            raise ValueError('invalid upstream repository')
        suffix = 'tags/' + quote(tag, safe='') if tag else 'latest'
        return self.request('GET', f'/repos/{repository}/releases/{suffix}', missing_ok=True)

    def alert(self):
        # List rather than search: a freshly created alert must block the next run.
        page = 1
        while True:
            issues = self.request('GET', f'/repos/{self.repository}/issues?state=open&per_page=100&page={page}')
            for issue in issues:
                if 'pull_request' not in issue and ISSUE_MARKER in (issue.get('body') or ''):
                    return issue
            if len(issues) < 100:
                return None
            page += 1


def git(*args, check=True):
    result = subprocess.run(['git', *args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f'git {args[0]} failed: ' + (result.stderr or result.stdout).strip())
    return result


def output(key, value):
    destination = os.environ.get('GITHUB_OUTPUT')
    if destination:
        with Path(destination).open('a') as stream:
            stream.write(f'{key}={value}\n')


def summary(message):
    print(message)
    destination = os.environ.get('GITHUB_STEP_SUMMARY')
    if destination:
        with Path(destination).open('a') as stream:
            stream.write(message + '\n\n')


def read_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def write_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n')


def report(**data):
    Path(os.environ.get('SYNC_REPORT', 'upstream-sync-report.json')).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def configure_git():
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')


def merge_release(upstream_sha, tag):
    """Merge upstream code while retaining the fork's root README files."""
    result = git('merge', '--no-ff', '--no-commit', upstream_sha, check=False)
    conflicts = git('diff', '--name-only', '--diff-filter=U', '-z').stdout
    paths = [path for path in conflicts.split('\0') if path]
    if result.returncode and not paths:
        report(tag=tag, upstream_sha=upstream_sha, conflicts=[],
               error='merge failed', log=result.stdout + result.stderr)
        git('merge', '--abort', check=False)
        raise RuntimeError('upstream merge failed')

    # Root README files describe this fork. Preserve them even when an upstream
    # edit merges cleanly, including the fork's intentional deletions.
    existing = set(git('ls-tree', '--name-only', '-z', 'HEAD', '--', *FORK_READMES).stdout.split('\0'))
    retained = [path for path in FORK_READMES if path in existing]
    deleted = [path for path in FORK_READMES if path not in existing]
    if retained:
        git('restore', '--source=HEAD', '--staged', '--worktree', '--', *retained)
    if deleted:
        git('rm', '-f', '--ignore-unmatch', '--', *deleted)
    paths = [path for path in paths if path not in FORK_READMES]
    if result.returncode:
        # VERSION is generated from the fork tag, so resolve only this metadata file.
        version_path = 'backend/cmd/server/VERSION'
        if version_path in paths:
            Path(version_path).write_text(tag.removeprefix('v') + '\n')
            git('add', version_path)
            paths.remove(version_path)
        if not paths:
            return
        report(tag=tag, upstream_sha=upstream_sha, conflicts=paths,
               error='merge conflict' if paths else 'merge failed', log=result.stdout + result.stderr)
        git('merge', '--abort', check=False)
        raise RuntimeError('upstream merge conflict: ' + ', '.join(paths) if paths else 'upstream merge failed')


def select_tag(upstream_tag, release, state, revision):
    """Blank input is idempotent; 'next' explicitly builds a new fork revision."""
    same = (state.get('upstream_tag', state.get('tag')) == upstream_tag
            and state.get('release_id') == release['id'])
    if same and not state.get('published') and FORK_TAG_RE.fullmatch(state.get('tag', '')):
        if revision and revision not in ('next', str(state.get('revision'))):
            raise ValueError('finish or retry the pending revision before requesting another')
        return state['tag']
    if (same and state.get('published') and not revision
            and FORK_TAG_RE.fullmatch(state.get('tag', ''))):
        return None
    if revision == 'next':
        pattern = re.compile(re.escape(upstream_tag) + r'-([1-9]\d*)')
        revisions = [int(match[1]) for tag in git('tag', '--list', upstream_tag + '-*').stdout.splitlines()
                     if (match := pattern.fullmatch(tag))]
        if same and state.get('revision'):
            revisions.append(state['revision'])
        number = max(revisions, default=0) + 1
    elif revision:
        if not re.fullmatch(r'[1-9]\d*', revision):
            raise ValueError('revision must be a positive integer or next')
        number = int(revision)
    else:
        number = 1
    if same and state.get('published') and number <= state.get('revision', 0):
        raise ValueError('revision must be newer than the published fork revision')
    return f'{upstream_tag}-{number}'


def prepare_tag(tag, upstream_sha, release):
    """Return an immutable customized tag, or refuse a pre-existing unrelated tag."""
    if not FORK_TAG_RE.fullmatch(tag) or tag.rsplit('-', 1)[0] != release['tag_name']:
        raise ValueError('fork tag must be the upstream tag followed by a positive revision')
    state = read_state()
    tagged = git('rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}', check=False)
    if tagged.returncode == 0:
        tagged_state = git('show', f'refs/tags/{tag}:{STATE}', check=False)
        metadata = json.loads(tagged_state.stdout) if tagged_state.returncode == 0 else {}
        if metadata.get('tag') != tag or metadata.get('upstream_sha') != upstream_sha:
            raise RuntimeError(f'{tag} already exists and is not a managed BNDS release; refusing to replace it')
        if git('merge-base', '--is-ancestor', tagged.stdout.strip(), 'HEAD', check=False).returncode:
            raise RuntimeError('release tag is not an ancestor of the default branch')
        return tagged.stdout.strip()
    # Avoid accidentally applying an older release on top of a newer pending merge.
    if state.get('tag') == tag and state.get('upstream_sha') != upstream_sha:
        raise RuntimeError('upstream moved a previously synchronized tag')
    merge_release(upstream_sha, tag)
    version_file = Path('backend/cmd/server/VERSION')
    version_file.write_text(tag[1:] + '\n')
    write_state({'upstream_repository': os.environ['UPSTREAM_REPOSITORY'],
                 'upstream_tag': release['tag_name'], 'revision': int(tag.rsplit('-', 1)[1]), 'tag': tag,
                 'upstream_sha': upstream_sha, 'release_id': release['id'],
                 'published_at': release['published_at'], 'published': False})
    git('add', str(STATE), str(version_file))
    git('commit', '-m', f'chore: build {tag} from upstream {release["tag_name"]} with BNDS frontend')
    notes = (f'BNDS AI普及计划 — {tag}\n\n'
             f'Upstream release: {release["html_url"]}\n'
             f'Upstream commit: {upstream_sha}\n\n'
             'Built from this fork with the BNDS frontend.\n\n' + (release.get('body') or ''))
    subprocess.run(['git', 'tag', '-a', tag, '-F', '-'], input=notes, text=True, check=True)
    return git('rev-parse', 'HEAD').stdout.strip()


def sync(api):
    output('ready', 'false')
    alert = api.alert()
    if alert and os.environ.get('MANUAL_SYNC') != 'true':
        summary(f'Automatic sync paused: {alert["html_url"]}. Resolve the alert and run this workflow manually.')
        return
    requested = os.environ.get('REQUESTED_TAG', '').strip()
    if requested and not TAG_RE.fullmatch(requested):
        raise ValueError('expected a v-prefixed version tag')
    release = api.release(requested, upstream=True)
    if not release:
        if requested:
            raise ValueError('requested upstream release does not exist')
        summary('No stable upstream release is available.')
        return
    upstream_tag = release['tag_name']
    if not TAG_RE.fullmatch(upstream_tag) or release.get('draft') or (not requested and release.get('prerelease')):
        raise ValueError('expected a published version release')
    state = read_state()
    revision = os.environ.get('REQUESTED_REVISION', '').strip()
    if revision and os.environ.get('MANUAL_SYNC') != 'true':
        raise ValueError('new revisions must be requested manually')
    tag = select_tag(upstream_tag, release, state, revision)
    if tag is None:
        summary(f'{upstream_tag} is already published by this fork as {state["tag"]}.')
        return
    output('tag', tag)
    report(tag=tag, upstream_tag=upstream_tag, upstream_url=release['html_url'])
    if (state.get('published_at') and release['published_at'] < state['published_at']
            and state.get('upstream_tag', state.get('tag')) != upstream_tag):
        raise ValueError('refusing to roll the default branch back to an older release')
    if api.release(tag):
        # A release not recorded by this automation must not be silently overwritten.
        raise RuntimeError(f'fork release {tag} already exists without a completed sync record; inspect it before retrying')
    # The report is outside the Git worktree in Actions.
    if git('status', '--porcelain', '--untracked-files=no').stdout:
        raise RuntimeError('sync requires a clean checkout')
    configure_git()
    upstream = os.environ['UPSTREAM_REPOSITORY']
    if not REPO_RE.fullmatch(upstream):
        raise ValueError('invalid upstream repository')
    # Never fetch upstream tags into the fork tag namespace.
    git('fetch', '--no-tags', f'https://github.com/{upstream}.git',
        f'+refs/tags/{upstream_tag}:refs/upstream-release/{upstream_tag}')
    upstream_sha = git('rev-parse', f'refs/upstream-release/{upstream_tag}^{{commit}}').stdout.strip()
    fork_sha = prepare_tag(tag, upstream_sha, release)
    # No force push. Branch races or tag collisions fail atomically.
    git('push', '--atomic', 'origin', f'HEAD:refs/heads/{os.environ["SYNC_BRANCH"]}',
        f'refs/tags/{tag}:refs/tags/{tag}')
    report(tag=tag, upstream_tag=upstream_tag, upstream_url=release['html_url'], upstream_sha=upstream_sha, fork_sha=fork_sha)
    output('ready', 'true')
    summary(f'Synchronized {tag}: upstream `{upstream_sha}`, customized fork `{fork_sha}`. Starting the release build.')


def finish(api):
    tag = os.environ['REQUESTED_TAG']
    if not FORK_TAG_RE.fullmatch(tag):
        raise ValueError('invalid fork release tag')
    state = read_state()
    published = api.release(tag)
    if state.get('tag') != tag or not published or published.get('draft'):
        raise RuntimeError('cannot record success without the matching published release')
    configure_git()
    if not state.get('published'):
        state['published'] = True
        write_state(state)
        git('add', str(STATE))
        git('commit', '-m', f'chore: record upstream release {tag} publication [skip ci]')
        git('push', 'origin', f'HEAD:refs/heads/{os.environ["SYNC_BRANCH"]}')
    alert = api.alert()
    if alert:
        api.request('POST', f'/repos/{api.repository}/issues/{alert["number"]}/comments',
                    {'body': f'Sync and publication completed: {published["html_url"]}'})
        api.request('PATCH', f'/repos/{api.repository}/issues/{alert["number"]}', {'state': 'closed'})
    summary(f'Published {tag}: {published["html_url"]}')


def notify(api):
    path = Path(os.environ.get('SYNC_REPORT', 'upstream-sync-report.json'))
    data = json.loads(path.read_text()) if path.exists() else {}
    tag = data.get('tag') or os.environ.get('REQUESTED_TAG') or 'unknown release'
    run_url = f'https://github.com/{api.repository}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
    users = [user.strip().lstrip('@') for user in os.environ.get('NOTIFY_USERS', '').split(',')]
    mentions = ' '.join('@' + user for user in users if re.fullmatch(r'[A-Za-z0-9-]+', user))
    conflicts = data.get('conflicts', [])
    details = '\n'.join('- `' + path.replace('`', '') + '`' for path in conflicts)
    body = (f'{ISSUE_MARKER}\n{mentions}\n\n'
            f'上游 **{tag}** 自动同步或发布失败。\n\n'
            f'- Actions: {run_url}\n'
            f'- Job results: {os.environ.get("SYNC_RESULTS", "unknown")}\n\n'
            + ('冲突文件：\n' + details + '\n\n' if conflicts else '')
            + '已暂停后续自动同步。默认分支不会写入未解决的合并，发布标签不会被强制覆盖。\n\n'
            '请查看 Actions 日志及 upstream-sync-report，解决冲突后提交到默认分支，'
            '再手动运行 Sync upstream release。未发布标签的构建重试使用原提交；'
            '若修复需要改代码，请先检查并移除该未发布的标签，再重试。'
            '已存在的 Release 需要人工确认，不会自动覆盖。')
    alert = api.alert()
    title = f'[Upstream sync] {tag} needs attention'
    if alert:
        issue = api.request('PATCH', f'/repos/{api.repository}/issues/{alert["number"]}',
                            {'title': title, 'body': body})
    else:
        issue = api.request('POST', f'/repos/{api.repository}/issues', {'title': title, 'body': body})
    summary('Sync alert: ' + issue['html_url'])
    token, chat_id = os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        request = Request(f'https://api.telegram.org/bot{token}/sendMessage',
                          data=json.dumps({'chat_id': chat_id, 'text':
                                           f'BNDS AI普及计划：上游 {tag} 同步/发布失败。\n{issue["html_url"]}\n{run_url}'}).encode(),
                          headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=30) as response:
                if not json.loads(response.read()).get('ok'):
                    print('::warning::Telegram notification was not accepted')
        except Exception:
            print('::warning::Telegram notification failed; the GitHub Issue is available')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sync', 'finish', 'notify'])
    args = parser.parse_args()
    api = GitHub(os.environ['GITHUB_REPOSITORY'])
    try:
        {'sync': sync, 'finish': finish, 'notify': notify}[args.command](api)
    except Exception as error:
        print(f'::error::{error}', file=sys.stderr)
        if args.command == 'sync':
            path = Path(os.environ.get('SYNC_REPORT', 'upstream-sync-report.json'))
            data = json.loads(path.read_text()) if path.exists() else {}
            report(**{**data, 'error': str(error)})
        raise SystemExit(1)


if __name__ == '__main__':
    main()
