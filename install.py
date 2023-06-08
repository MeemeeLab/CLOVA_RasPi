import os
import pwd
import sys

username = pwd.getpwuid(os.getuid()).pw_name
group_id = str(os.getgid())

if username == "root":
    if len(sys.argv) != 3:
        print("rootとして実行しないでください")
        exit(1)

    username = sys.argv[1]
    group_id = sys.argv[2]

    print(f"{username}としてインストールします。")

    script_directory = os.path.dirname(os.path.abspath(__file__))

    service_file_path = os.path.join(script_directory, "assets/clova.service")
    launcher_path = os.path.join(script_directory, "launcher.py")
    launcher_dir = script_directory

    with open(service_file_path, "r") as file:
        service_content = file.read()

    service_content = service_content.replace("{LAUNCHER_PATH}", launcher_path)
    service_content = service_content.replace("{LAUNCHER_DIR}", launcher_dir)
    service_content = service_content.replace("{USERNAME}", username)
    service_content = service_content.replace("{GROUP_ID}", group_id)

    systemd_service_path = "/etc/systemd/system/clova.service"
    with open(systemd_service_path, "w") as file:
        file.write(service_content)

    print(f"clova.serviceファイルは以下に書き込まれました: '{systemd_service_path}'")

    exit(0)

os.execvp("sudo", ["sudo", sys.executable, sys.argv[0], username, group_id])
