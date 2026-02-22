import os

# 删除数据库文件
db_path = "data.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ 已删除 {db_path}")
else:
    print(f"✗ {db_path} 不存在")

print("\n请重新启动服务器以重新初始化数据库")
print("运行: uvicorn main:app --reload --port 8001")
