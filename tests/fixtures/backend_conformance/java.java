package fixture;

import java.util.concurrent.CompletableFuture;
import support.Service;

class BaseWorker {
}

class Worker<T> extends BaseWorker {
    T run(T item) {
        helper(item);
        helper(item);
        return item;
    }

    T helper(T item) {
        return item;
    }

    CompletableFuture<T> async_probe(T item) {
        return CompletableFuture.completedFuture(item);
    }

    T nested_probe(T item) {
        java.util.function.Function<T, T> nested = value -> value;
        return nested.apply(item);
    }
}
