"""Offline checks for supported links and Bilibili's complete-video choice."""

import importlib.util
import struct
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "download_douyin.py"
SPEC = importlib.util.spec_from_file_location("snapany_downloader", SCRIPT)
downloader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(downloader)


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def small_mp4(*handlers: bytes) -> bytes:
    tracks = b"".join(
        box(b"trak", box(b"mdia", box(b"hdlr", b"\0" * 8 + handler + b"\0" * 4)))
        for handler in handlers
    )
    return box(b"ftyp", b"isom\0\0\0\0") + box(b"moov", tracks)


class LinkTests(unittest.TestCase):
    def test_mixed_share_text_preserves_order_and_deduplicates(self):
        text = (
            "B站 https://b23.tv/abc。抖音 https://v.douyin.com/xyz/！"
            "原站 https://www.bilibili.com/video/BV123?spm_id_from=1 "
            "重复 https://b23.tv/abc"
        )
        self.assertEqual(
            downloader.video_urls(text),
            ["https://b23.tv/abc", "https://v.douyin.com/xyz/",
             "https://www.bilibili.com/video/BV123?spm_id_from=1"],
        )
        self.assertEqual(downloader.douyin_urls(text), ["https://v.douyin.com/xyz/"])

    def test_rejects_lookalike_and_credentials(self):
        for url in (
            "https://bilibili.com.evil.example/video/BV1",
            "https://b23.tv.evil.example/a",
            "https://douyin.com.evil.example/video/1",
            "https://user@bilibili.com/video/BV1",
        ):
            with self.subTest(url=url):
                self.assertIsNone(downloader.platform_for_url(url))


class BilibiliMediaTests(unittest.TestCase):
    def setUp(self):
        public_dns = [(downloader.socket.AF_INET, downloader.socket.SOCK_STREAM,
                       6, "", ("8.8.8.8", 443))]
        dns_patch = mock.patch.object(downloader.socket, "getaddrinfo", return_value=public_dns)
        dns_patch.start()
        self.addCleanup(dns_patch.stop)
        self.video = {
            "resource_url": "https://media.example/complete.mp4",
            "variants": [
                {"quality": 720, "video_url": "https://media.example/720-video.m4s",
                 "audio_url": "https://media.example/720-audio.m4s"},
                {"quality": 1080, "is_default": True,
                 "video_url": "https://media.example/1080-video.m4s",
                 "audio_url": "https://media.example/1080-audio.m4s"},
            ],
        }

    def test_uses_default_separate_tracks_with_ffmpeg(self):
        kind, source = downloader.choose_bilibili_source(self.video, True)
        self.assertEqual(kind, "mux")
        self.assertEqual(source["quality"], 1080)

    def test_without_ffmpeg_only_considers_direct_mp4(self):
        kind, source = downloader.choose_bilibili_source(self.video, False)
        self.assertEqual((kind, source), ("resource", self.video["resource_url"]))
        without_direct = dict(self.video, resource_url="")
        with self.assertRaises(downloader.DownloadError):
            downloader.choose_bilibili_source(without_direct, False)

    def test_media_url_and_redirect_reject_local_targets(self):
        for url in (
            "https://user:secret@media.example/video.mp4",
            "https://media.example:0/video.mp4",
            "https://media.example:65536/video.mp4",
            "http://localhost/video.mp4",
            "http://127.0.0.1/video.mp4",
            "http://192.168.200.123/video.mp4",
            "http://[::1]/video.mp4",
            "http://2130706433/video.mp4",
        ):
            with self.subTest(url=url):
                self.assertFalse(downloader._valid_media_url(url))
                with self.assertRaises(downloader.DownloadError):
                    downloader._SafeMediaRedirectHandler().redirect_request(
                        urllib.request.Request("https://media.example/start"),
                        None, 302, "Found", {}, url,
                    )
        self.assertTrue(downloader._valid_media_url("https://media.example/video.mp4"))
        self.assertTrue(downloader._valid_media_url("https://media.example:4483/video.m4s"))
        self.assertTrue(downloader._valid_media_url("http://media.example:8082/audio.m4s"))

    def test_private_dns_result_is_rejected_for_media_and_redirect(self):
        private_dns = [(downloader.socket.AF_INET, downloader.socket.SOCK_STREAM,
                        6, "", ("10.0.0.2", 443))]
        with mock.patch.object(downloader.socket, "getaddrinfo", return_value=private_dns):
            self.assertFalse(downloader._valid_media_url("https://media.example/video.mp4"))
            with self.assertRaises(downloader.DownloadError):
                downloader._SafeMediaRedirectHandler().redirect_request(
                    urllib.request.Request("https://media.example/start"),
                    None, 302, "Found", {}, "https://media.example/private.mp4",
                )

    def test_proxy_can_resolve_when_local_dns_is_unavailable(self):
        with mock.patch.object(downloader.socket, "getaddrinfo", side_effect=OSError):
            with mock.patch.object(downloader.urllib.request, "getproxies",
                                   return_value={"https": "http://proxy.example:3128"}):
                with mock.patch.object(downloader.urllib.request, "proxy_bypass",
                                       return_value=False):
                    self.assertTrue(downloader._valid_media_url(
                        "https://media.example/video.mp4"
                    ))

    def test_douyin_download_uses_safe_media_opener(self):
        with tempfile.TemporaryDirectory() as folder:
            video = {"resource_url": "https://media.example/video.mp4", "headers": {}}
            with mock.patch.object(downloader, "extract_video", return_value=("123456", video)):
                with mock.patch.object(downloader._MEDIA_OPENER, "open",
                                       side_effect=downloader.DownloadError("unsafe redirect")) as opener:
                    with mock.patch.object(downloader.urllib.request, "urlopen",
                                           side_effect=AssertionError("unsafe opener")):
                        with self.assertRaises(downloader.DownloadError):
                            downloader.download("https://v.douyin.com/abc/", Path(folder))
                    opener.assert_called_once()

    def test_bilibili_forwards_only_public_media_headers(self):
        headers = downloader._media_headers(
            {"headers": {"User-Agent": "test-agent", "Referer": "https://www.bilibili.com/",
                         "Authorization": "private", "Cookie": "private"}},
            "bilibili",
        )
        self.assertEqual(headers, {"User-Agent": "test-agent",
                                   "Referer": "https://www.bilibili.com/"})

    def test_douyin_forwards_only_public_media_headers(self):
        headers = downloader._media_headers(
            {"headers": {"User-Agent": "test-agent", "Referer": "https://www.douyin.com/",
                         "Origin": "https://www.douyin.com", "Accept": "video/mp4",
                         "Accept-Language": "zh", "Authorization": "private",
                         "Cookie": "private"}},
            "douyin",
        )
        self.assertEqual(headers, {
            "User-Agent": "test-agent", "Referer": "https://www.douyin.com/",
            "Origin": "https://www.douyin.com", "Accept": "video/mp4",
            "Accept-Language": "zh",
        })
        with self.assertRaises(downloader.DownloadError):
            downloader._media_headers(
                {"headers": {"Referer": "https://www.douyin.com/\r\nCookie: private"}},
                "douyin",
            )

    def test_direct_mp4_must_have_video_and_audio_tracks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "media.mp4"
            path.write_bytes(small_mp4(b"vide", b"soun"))
            self.assertTrue(downloader.mp4_has_video_and_audio(path))
            path.write_bytes(small_mp4(b"vide"))
            self.assertFalse(downloader.mp4_has_video_and_audio(path))
            path.write_bytes(small_mp4(b"soun"))
            self.assertFalse(downloader.mp4_has_video_and_audio(path))
            path.write_bytes(b"not an mp4")
            self.assertFalse(downloader.mp4_has_video_and_audio(path))

    def test_completed_files_use_bilibili_prefix_without_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "source.mp4"
            source.write_bytes(small_mp4(b"vide", b"soun"))
            first = downloader._publish_media(source, directory, "abc123")
            second = downloader._publish_media(source, directory, "abc123")
            self.assertEqual(first.name, "bilibili-abc123.mp4")
            self.assertEqual(second.name, "bilibili-abc123-2.mp4")
            self.assertEqual(first.read_bytes(), source.read_bytes())

    def test_no_ffmpeg_delivers_only_direct_mp4_with_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            with mock.patch.object(downloader.shutil, "which", return_value=None):
                with mock.patch.object(
                    downloader, "_download_media",
                    side_effect=lambda url, path, headers: path.write_bytes(
                        small_mp4(b"vide", b"soun")
                    ),
                ):
                    saved = downloader._download_bilibili("abc123", self.video, directory, {})
                self.assertEqual(saved.name, "bilibili-abc123.mp4")
                with mock.patch.object(
                    downloader, "_download_media",
                    side_effect=lambda url, path, headers: path.write_bytes(small_mp4(b"vide")),
                ):
                    with self.assertRaises(downloader.DownloadError):
                        downloader._download_bilibili("different", self.video, directory, {})
            self.assertFalse((directory / "bilibili-different.mp4").exists())

    def test_failed_default_mux_uses_complete_direct_mp4(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            urls = []

            def fake_download(url, path, headers):
                urls.append(url)
                path.write_bytes(b"separate track" if url != self.video["resource_url"]
                                 else small_mp4(b"vide", b"soun"))

            with mock.patch.object(downloader.shutil, "which", return_value="ffmpeg"):
                with mock.patch.object(downloader, "_download_media", side_effect=fake_download):
                    with mock.patch.object(downloader.subprocess, "run") as ffmpeg_run:
                        ffmpeg_run.return_value.returncode = 1
                        saved = downloader._download_bilibili("abc123", self.video, directory, {})
            self.assertEqual(saved.name, "bilibili-abc123.mp4")
            self.assertEqual(urls[-1], self.video["resource_url"])
            self.assertTrue(downloader.mp4_has_video_and_audio(saved))


if __name__ == "__main__":
    unittest.main()
