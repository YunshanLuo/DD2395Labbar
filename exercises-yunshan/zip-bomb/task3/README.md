## Task 3

Now that you can create non-recursive zip bombs of varying sizes, it is time to create a detector that can determine if a `.zip` file is a zip bomb or a normal zip file. There are some different ways that a zip bomb differs from a normal zip file, use that to your advantage. It is important that your solution at no point unzips the `.zip` file. This is because unzipping a zip bomb, as you know, can be harmful to your device and you want to use your detector to avoid that.

You can verify that your code passes the tests by running
`python3 -m test` in this directory.
