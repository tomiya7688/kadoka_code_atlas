extends RefCounted

const Support = preload("res://support.gd")


class BaseWorker:
    pass


class Worker extends BaseWorker:
    func run(item: Variant) -> Variant:
        helper(item)
        helper(item)
        return item

    func helper(item: Variant) -> Variant:
        return item

    func async_probe(item: Variant) -> Variant:
        await Engine.get_main_loop().process_frame
        return item

    func nested_probe(item: Variant) -> Variant:
        var nested := func(value: Variant) -> Variant:
            return value
        return nested.call(item)

    func typed_container_probe(items: Array[Variant]) -> Array[Variant]:
        return items
