package fixture

import (
    "example/support"
)

type BaseWorker struct{}

type Worker[T any] struct {
    BaseWorker
}

func (w Worker[T]) run(item T) T {
    w.helper(item)
    w.helper(item)
    return item
}

func (w Worker[T]) helper(item T) T {
    return item
}

func (w Worker[T]) async_probe(item T) T {
    done := make(chan T, 1)
    go func(value T) {
        support.Touch(value)
        done <- value
    }(item)
    return <-done
}

func (w Worker[T]) nested_probe(item T) T {
    nested := func(value T) T { return value }
    return nested(item)
}
