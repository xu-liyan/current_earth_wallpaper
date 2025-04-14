# 从当前环境中复制 cacert.pem 到项目目录（例如 certs/ 子目录）：

# save_as_copy_certifi_cert.py
import certifi
import shutil
import os

def copy_certifi_cert():
    # 获取证书源路径
    src_path = certifi.where()
    print(f"[1/3] 证书源文件路径: {src_path}")

    # 创建目标目录 (./certs)
    dest_dir = os.path.join(os.getcwd(), "certs")
    os.makedirs(dest_dir, exist_ok=True)
    print(f"[2/3] 已创建目标目录: {dest_dir}")

    # 构建目标路径
    dest_path = os.path.join(dest_dir, "cacert.pem")

    try:
        # 复制证书文件
        shutil.copy(src_path, dest_path)
        print(f"[3/3] 成功! 证书已复制到: {dest_path}")
        return True
    except Exception as e:
        print(f"[3/3] 错误! 复制失败: {str(e)}")
        return False

if __name__ == "__main__":
    copy_certifi_cert()