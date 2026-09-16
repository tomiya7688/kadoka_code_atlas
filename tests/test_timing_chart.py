from Src.generators.timing_chart import build_timing_chart_bundle
from Src.languages.python_timing import PythonTimingLanguageAdapter
from Src.renderers.mermaid_timing_chart import render_timing_chart


def test_python_timing_extracts_async_wait_parallel_sync_and_periodic_relations() -> None:
    module = PythonTimingLanguageAdapter().parse(
        """
import asyncio

async def pipeline(lock):
    task = asyncio.create_task(fetch())
    await asyncio.sleep(1)
    async with lock:
        await save()
    await asyncio.gather(cleanup(), notify())
    while True:
        await tick()
"""
    )

    flow = module.timing_flows[0]
    assert flow.owner == "pipeline"
    assert flow.is_async is True
    kinds = [event.kind for event in flow.events]
    assert kinds == [
        "parallel_start",
        "wait",
        "sync",
        "await",
        "parallel_start",
        "parallel_start",
        "parallel_join",
        "periodic",
        "await",
    ]
    assert flow.events[0].target == "fetch"
    assert flow.events[1].target == "asyncio.sleep"
    assert flow.events[3].target == "save"
    assert [event.target for event in flow.events[4:6]] == ["cleanup", "notify"]
    assert [event.order for event in flow.events] == list(range(1, 10))


def test_python_timing_extracts_timer_callback_and_sync_wait() -> None:
    module = PythonTimingLanguageAdapter().parse(
        """
def schedule(loop, future, lock):
    loop.call_later(1.5, refresh)
    future.add_done_callback(done)
    lock.acquire()
"""
    )

    events = module.timing_flows[0].events
    assert [(event.kind, event.target) for event in events] == [
        ("timer", "refresh"),
        ("callback", "done"),
        ("sync_wait", "lock.acquire"),
    ]
    assert events[0].detail == "1.5"


def test_timing_chart_generator_and_mermaid_renderer_preserve_logical_order() -> None:
    module = PythonTimingLanguageAdapter().parse(
        """
async def load():
    prepare()
    await fetch()
"""
    )
    bundle = build_timing_chart_bundle(module)

    assert bundle.statistics["chart_count"] == 1
    assert bundle.statistics["async_flow_count"] == 1
    assert bundle.statistics["await_count"] == 1
    chart = bundle.charts[0]
    rendered = render_timing_chart(chart)
    assert rendered.startswith("sequenceDiagram\n")
    assert 'participant p0 as "load"' in rendered
    assert "1. call prepare" in rendered
    assert "2. await fetch" in rendered
    assert "resume" in rendered
    assert "ms" not in rendered
    assert "seconds" not in rendered
