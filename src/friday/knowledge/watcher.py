"""文件监控 — watchdog 目录监控 + 增量索引"""

import logging
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent
from watchdog.observers import Observer

from friday.knowledge.store import NOTES_DIR, read_note_file, validate_note_id

logger = logging.getLogger(__name__)

_observer: Observer | None = None

_SUPPORTED_EXTENSIONS = {".md", ".txt"}


class _KnowledgeHandler(FileSystemEventHandler):
    """知识目录文件变化处理器"""

    def on_created(self, event: FileCreatedEvent) -> None:
        path = Path(event.src_path)
        if not _is_supported(path):
            return
        logger.info(f"检测到新文件: {path}")
        _index_file(path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        path = Path(event.src_path)
        if not _is_supported(path):
            return
        logger.info(f"检测到文件修改: {path}")
        _reindex_file(path)

    def on_deleted(self, event: FileDeletedEvent) -> None:
        path = Path(event.src_path)
        if not _is_supported(path):
            return
        logger.info(f"检测到文件删除: {path}")
        _remove_index(path)


def _is_supported(path: Path) -> bool:
    """判断文件是否为支持的类型"""
    return path.suffix.lower() in _SUPPORTED_EXTENSIONS and not path.name.startswith(".")


def _index_file(path: Path) -> None:
    """为新文件建立索引"""
    try:
        note = read_note_file(path)
        if not note.id or not note.content.strip():
            return
        from friday.knowledge.adapter import index_note
        index_note(note, str(path))
    except Exception as e:
        logger.warning(f"索引文件失败 {path}: {e}")


def _reindex_file(path: Path) -> None:
    """重新索引修改的文件"""
    try:
        note = read_note_file(path)
        if not note.id:
            return
        from friday.knowledge.adapter import reindex_note
        reindex_note(note.id)
    except Exception as e:
        logger.warning(f"重新索引失败 {path}: {e}")


def _remove_index(path: Path) -> None:
    """移除已删除文件的索引"""
    note_id = path.stem
    try:
        validate_note_id(note_id)
    except ValueError:
        return
    from friday.knowledge.adapter import delete_note
    try:
        delete_note(note_id)
    except Exception:
        pass


def start_watcher(directory: Path | None = None) -> None:
    """启动文件监控"""
    global _observer
    if _observer is not None:
        return
    watch_dir = directory or NOTES_DIR
    watch_dir.mkdir(parents=True, exist_ok=True)
    _observer = Observer()
    _observer.schedule(_KnowledgeHandler(), str(watch_dir), recursive=True)
    _observer.start()
    logger.info(f"文件监控已启动: {watch_dir}")


def stop_watcher() -> None:
    """停止文件监控"""
    global _observer
    if _observer is None:
        return
    _observer.stop()
    _observer.join(timeout=5)
    _observer = None
    logger.info("文件监控已停止")
