# Purpose

When parsing Linux/Android logs, we often use various tools to filter the logs. However, I haven't found a tool that can save multiple regular expressions and search across multiple files simultaneously. Some systems print each log line to different files, making it challenging to find the logs you need.

While experienced Linux users can write commands with `find`, `grep`, `awk`, and `sed` in bash to search patterns in multiple files, the bash syntax is not very user-friendly.

# Usage Example

This example demonstrates how to parse the dumpState log from a Samsung A15 phone. Note that this example uses only one log file for filtering, which is not ideal.

1. Dump logs following these steps:
   [Get device logs - Samsung Knox Documentation](https://docs.samsungknox.com/admin/knox-platform-for-enterprise/troubleshoot/get-device-logs/)

2. Apply the filter on the log:
   ```bash
   ./mfmf_cli.py -l my_log_dir -c ./example_config > output.txt
   ```

3. Enable advanced feature: "exec() script"
   ```bash
   ./mfmf_cli.py -l my_log_dir -c ./example_config --exec_script > output.txt
   ```

# TODO List

1. Provide a comprehensive example involving scattered logs.
2. Implement auto-unzip functionality for files in the log directory.
3. DONE: Implement "exec() script" for filtering by comparing numbers in the log.
4. Refactor source code
5. Add unit test
6. Add -h to show helps
7. Output to files instead of only stdout
8. Add GUI support
9. Support json configs (json config is more easier to maintain if we have a GUI)
