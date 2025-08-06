#!/usr/bin/env python3
"""
測試修復後的 Python 相容性
"""
import sys

def test_python_version():
    """測試 Python 版本"""
    print("🐍 Python 版本檢查...")
    version = sys.version_info
    print(f"當前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 13):
        print("⚠️  警告：Python 3.13+ 可能有 aiohttp 相容性問題")
        print("建議使用 Python 3.11.9")
        return False
    elif version >= (3, 11):
        print("✅ Python 版本適合")
        return True
    else:
        print("⚠️  Python 版本可能過舊，建議升級到 3.11+")
        return True

def test_package_compatibility():
    """測試套件相容性"""
    print("\n📦 套件相容性檢查...")
    
    packages_to_test = [
        ("aiohttp", "3.9.1"),
        ("line-bot-sdk", "3.12.0"), 
        ("fastapi", "0.104.1"),
        ("sqlalchemy", "2.0.23"),
        ("psycopg2", None),
        ("gunicorn", "21.2.0")
    ]
    
    all_good = True
    
    for package, expected_version in packages_to_test:
        try:
            if package == "psycopg2":
                import psycopg2
                version = psycopg2.__version__
                print(f"✅ {package}: {version}")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package}: {version}")
                
                if expected_version and version != expected_version:
                    print(f"⚠️  版本不符，預期: {expected_version}")
                    
        except ImportError as e:
            print(f"❌ {package}: 未安裝 - {e}")
            all_good = False
    
    return all_good

def test_aiohttp_c_extensions():
    """特別測試 aiohttp C 擴充模組"""
    print("\n🔧 aiohttp C 擴充模組測試...")
    
    try:
        import aiohttp
        
        # 測試可能會出問題的功能
        from aiohttp import ClientSession
        from aiohttp.web import Application, Response
        
        print("✅ aiohttp 核心模組正常")
        
        # 嘗試建立基本物件（不實際執行網路請求）
        app = Application()
        resp = Response(text="test")
        
        print("✅ aiohttp 物件建立正常")
        
        # 檢查版本是否解決 Python 3.13 問題
        version = aiohttp.__version__
        if version >= "3.9.0":
            print(f"✅ aiohttp 版本 {version} 應該與 Python 3.11 相容")
        else:
            print(f"⚠️  aiohttp 版本 {version} 可能需要更新")
            
        return True
        
    except Exception as e:
        print(f"❌ aiohttp 測試失敗: {e}")
        if "'PyLongObject' has no member named 'ob_digit'" in str(e):
            print("💡 這是 Python 3.13 相容性問題，請降級到 Python 3.11")
        return False

def show_deployment_fix_summary():
    """顯示修復摘要"""
    print("\n" + "="*60)
    print("🔧 Python 3.13 相容性問題修復摘要")
    print("="*60)
    
    fixes = [
        "✅ 降級 Python 版本從 3.9.6 → 3.11.9",
        "✅ 更新 aiohttp 從 3.8.5 → 3.9.1 (支援新版 Python)",
        "✅ 更新 line-bot-sdk 從 3.5.0 → 3.12.0 (最新穩定版)",
        "✅ 更新 psycopg2-binary 從 2.9.7 → 2.9.9",
        "✅ 建立 runtime.txt 指定 Python 版本",
        "✅ 更新所有配置檔案的 Python 版本設定"
    ]
    
    for fix in fixes:
        print(fix)
    
    print("\n🎯 關鍵改動:")
    print("1. Python 3.11.9 是目前最穩定的版本，避免 3.13 的破壞性變更")
    print("2. aiohttp 3.9.1 修復了與新版 Python 的 C 擴充相容性")
    print("3. runtime.txt 確保 Render 使用正確的 Python 版本")
    
    print("\n📋 部署檢查清單:")
    print("🔲 git add .")
    print("🔲 git commit -m 'fix: 修復 Python 3.13 相容性問題'")
    print("🔲 git push origin main")
    print("🔲 Render 會自動重新部署")
    print("🔲 檢查部署日誌確認無錯誤")

if __name__ == "__main__":
    print("🔍 開始 Python 相容性測試...")
    
    version_ok = test_python_version()
    packages_ok = test_package_compatibility()
    aiohttp_ok = test_aiohttp_c_extensions()
    
    if version_ok and packages_ok and aiohttp_ok:
        print("\n🎉 所有相容性測試通過！")
        show_deployment_fix_summary()
    else:
        print("\n❌ 部分測試失敗，請檢查上方錯誤訊息")
        print("\n💡 建議:")
        print("1. 確保使用 Python 3.11.9")
        print("2. 重新安裝套件: pip install -r requirements.txt")
        print("3. 檢查套件版本是否正確")