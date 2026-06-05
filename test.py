def find_primes(n: int) -> list[int]:
    """
    Return a list of all prime numbers from 2 up to n (inclusive).

    Uses an optimized linear sieve (Euler's sieve) that operates only on
    odd numbers to achieve strict O(n) time complexity. Each composite
    odd number is marked exactly once by its smallest prime factor,
    eliminating redundant work present in the classic Sieve of
    Eratosthenes.

    Parameters
    ----------
    n : int
        The upper bound (inclusive) of the range to search for primes.
        Must be an integer. If n < 2, an empty list is returned.

    Returns
    -------
    list[int]
        A list of prime numbers in ascending order from 2 to n.

    Examples
    --------
    >>> find_primes(10)
    [2, 3, 5, 7]
    >>> find_primes(1)
    []
    >>> find_primes(20)
    [2, 3, 5, 7, 11, 13, 17, 19]
    """
    if n < 2:
        return []
    if n == 2:
        return [2]

    # We only store odd numbers starting from 3.
    # Index i corresponds to the odd number 2*i + 3.
    size = (n - 1) // 2
    is_prime = bytearray([1]) * size  # 1 means prime, 0 means composite

    primes: list[int] = []  # stores odd primes found so far

    # Linear sieve on odd numbers
    for i in range(3, n + 1, 2):
        idx = (i - 3) // 2
        if is_prime[idx]:
            primes.append(i)

        # Mark composites using the current number `i` and all primes <= smallest prime factor of `i`
        for p in primes:
            multiple = i * p
            if multiple > n:
                break
            multiple_idx = (multiple - 3) // 2
            is_prime[multiple_idx] = 0
            if i % p == 0:
                break

    # Collect results: 2 is handled explicitly, then all remaining odd primes
    result = [2]
    result.extend(2 * idx + 3 for idx, flag in enumerate(is_prime) if flag)
    return result

print(find_primes(50))
