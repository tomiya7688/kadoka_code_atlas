using System.Threading.Tasks;
using Support;

public class BaseWorker
{
}

public class Worker<T> : BaseWorker
{
    public T run(T item)
    {
        helper(item);
        helper(item);
        return item;
    }

    public T helper(T item) => item;

    public async Task<T> async_probe(T item)
    {
        await Task.Yield();
        return item;
    }

    public T nested_probe(T item)
    {
        T nested(T value) => value;
        return nested(item);
    }
}
