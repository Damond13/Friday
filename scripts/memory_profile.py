"""Friday 内存占用分析脚本 — 逐步加载各组件，测量内存增量"""

import os
import sys
import tracemalloc
import gc

# 禁用 Mem0 遥测
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("MEM0_TELEMETRY", "False")


def get_rss_mb() -> float:
    """获取当前进程 RSS 内存（MB）"""
    import psutil
    return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024


def measure(label: str, func, *args, **kwargs):
    """执行函数并测量内存增量"""
    gc.collect()
    before = get_rss_mb()
    result = func(*args, **kwargs)
    gc.collect()
    after = get_rss_mb()
    delta = after - before
    print(f"  {label:45s} | RSS: {after:8.1f} MB | Δ: {delta:+8.1f} MB")
    return result, delta


def main():
    print("=" * 80)
    print("Friday 内存占用分析")
    print("=" * 80)

    # Baseline
    import psutil
    gc.collect()
    baseline = get_rss_mb()
    print(f"\n{'Python 基线':45s} | RSS: {baseline:8.1f} MB | Δ:    +0.0 MB")
    print("-" * 80)

    # Step 1: Config
    print("\n[1/8] 加载配置...")
    measure("friday.config (get_llm_config)", lambda: __import__("friday.config", fromlist=["get_llm_config"]).get_llm_config())

    # Step 2: Session
    print("\n[2/8] 创建会话...")
    measure("friday.cli.session (create_session)", lambda: __import__("friday.cli.session", fromlist=["create_session"]).create_session())

    # Step 3: LLM adapter
    print("\n[3/8] 加载 LLM 适配器...")
    measure("friday.llm (chat function import)", lambda: __import__("friday.llm", fromlist=["chat"]))

    # Step 4: Embedding model (shared)
    print("\n[4/8] 加载共享 Embedding 模型...")
    _, emb_delta = measure("friday.knowledge.embedding (get_shared_model)",
                           lambda: __import__("friday.knowledge.embedding", fromlist=["get_shared_model"]).get_shared_model())

    # Step 5: Knowledge vector store (ChromaDB #1)
    print("\n[5/8] 加载知识库向量存储 (ChromaDB #1)...")
    measure("friday.knowledge.vector (init_vector)",
            lambda: __import__("friday.knowledge.vector", fromlist=["init_vector"]).init_vector())

    # Step 6: Knowledge FTS (SQLite + jieba)
    print("\n[6/8] 加载知识库 FTS 索引...")
    measure("friday.knowledge.fts (init_fts)",
            lambda: __import__("friday.knowledge.fts", fromlist=["init_fts"]).init_fts())

    # Step 7: Mem0 dynamic memory (ChromaDB #2 + possibly embedding #2)
    print("\n[7/8] 加载动态记忆系统 (Mem0 + ChromaDB #2)...")
    from friday.memory.dynamic import _get_memory
    mem0_instance, mem0_delta = measure("friday.memory.dynamic (_get_memory)", _get_memory)

    # Check if Mem0 has its own embedding model or is using shared
    if mem0_instance is not None:
        try:
            mem0_model = mem0_instance.embedding_model.model
            from friday.knowledge.embedding import get_shared_model
            shared = get_shared_model()
            is_shared = mem0_model is shared
            print(f"  {'  Mem0 使用共享 embedding 模型?':45s} | {'✓ 是' if is_shared else '✗ 否（重复加载！）'}")
        except Exception as e:
            print(f"  {'  Mem0 embedding 模型检查':45s} | 失败: {e}")

    # Step 8: Full agent + executors
    print("\n[8/8] 加载 Agent 循环和执行器...")
    measure("friday.llm.agent (run_agent_loop)", lambda: __import__("friday.llm.agent", fromlist=["run_agent_loop"]))
    measure("friday.llm.executors (get_executor)", lambda: __import__("friday.llm.executors", fromlist=["get_executor"]))

    # Summary
    print("\n" + "=" * 80)
    gc.collect()
    final = get_rss_mb()
    print(f"总内存占用: {final:.1f} MB ({final/1024:.2f} GB)")
    print(f"相比基线增量: {final - baseline:.1f} MB ({(final - baseline)/1024:.2f} GB)")
    print("=" * 80)

    # Top memory by tracemalloc
    print("\n--- tracemalloc Top 15 (by allocated size) ---")
    tracemalloc.start()
    # Re-import to capture allocations
    import importlib
    mods_to_reload = [m for m in sys.modules if m.startswith("friday")]
    print(f"(已加载 {len(mods_to_reload)} 个 friday 模块)")
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    for stat in top_stats[:15]:
        print(f"  {stat}")


if __name__ == "__main__":
    main()
