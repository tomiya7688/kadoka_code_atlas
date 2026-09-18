package fixture;

import java.util.concurrent.CompletableFuture;
import java.util.function.Function;
import support.Service;

interface WorkContract<T> {
    T run(T item);
}

class BaseWorker {
}

class Worker<T> extends BaseWorker implements WorkContract<T> {
    @Override
    public T run(T item) {
        helper(item);
        helper(item);
        return item;
    }

    T helper(T item) {
        return item;
    }

    T helper(T item, int count) {
        return item;
    }

    CompletableFuture<T> async_probe(T item) {
        return CompletableFuture.completedFuture(item);
    }

    T nested_probe(T item) {
        Function<T, T> nested = value -> value;
        return nested.apply(item);
    }
}
