# Side-channel

File `crypto.py` implements a simple [Feistel two rounds symmetric cipher
](https://en.wikipedia.org/wiki/Feistel_cipher), where each block consists of
two bytes (16 bits).  The round function `F` is implemented via a
substitution box `T`, which maps bytes to bytes.
The class `Crypto` implements `feistel_encrypt`, which performs one encryption.

The code uses a simulated direct-cache, which is implemented via the class
`Cache`. The cache has 32 lines and 8 bytes per line (i.e. 256 bytes in
total).
The `Cache` provides the methods `clean`, which clean the cache,
and`read_address(address)`, which reads an address from the memory and returns
the value and the (simulated) time to complete the request.


The implementation has a side channel, since the final state of the cache
depends on the key and encrypted message.

Write an attack that infers the possible values of the two bytes
of the input ciphertext.
You can probe the cache state by checking the access times of the
cache and you can observe the resulting ciphertext.
Your code must be written in the function `infer_plaintext` of `attack.py`, it
should take the resulting ciphertext and state of the cache after encryption,
and return two sets representing the possible values for the two input bytes.

To test your solution execute `./test.py`.
