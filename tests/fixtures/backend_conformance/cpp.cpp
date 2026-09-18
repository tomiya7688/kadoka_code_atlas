#include <future>
#include "support.hpp"

class BaseWorker {
};

template <typename T>
class Worker : public BaseWorker {
public:
    T run(T item) {
        helper(item);
        helper(item);
        return item;
    }

    T helper(T item) {
        return item;
    }

    std::future<T> async_probe(T item) {
        return std::async(std::launch::async, [item]() { return item; });
    }

    T nested_probe(T item) {
        auto nested = [](T value) { return value; };
        return nested(item);
    }
};
