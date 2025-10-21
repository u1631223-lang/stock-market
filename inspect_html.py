"""
HTML構造を調査するスクリプト
"""

import sys
sys.path.insert(0, 'src')

import requests
from bs4 import BeautifulSoup
from config import URLS, USER_AGENT

def inspect_html_structure(target="morning"):
    """HTML構造を調査"""

    url = URLS[target]
    print(f"調査URL: {url}\n")

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=30)

    print(f"HTTPステータス: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"レスポンスサイズ: {len(response.text)} 文字\n")

    soup = BeautifulSoup(response.text, "lxml")

    # すべてのtableを探す
    tables = soup.find_all("table")
    print(f"=== テーブル数: {len(tables)} ===\n")

    for i, table in enumerate(tables, 1):
        print(f"--- テーブル {i} ---")
        print(f"  class: {table.get('class')}")
        print(f"  id: {table.get('id')}")

        rows = table.find_all("tr")
        print(f"  行数: {len(rows)}")

        # 最初の3行を表示
        for j, row in enumerate(rows[:3], 1):
            cells = row.find_all(["td", "th"])
            cell_texts = [cell.get_text(strip=True)[:20] for cell in cells]
            print(f"    行{j}: {len(cells)}セル -> {cell_texts}")

        print()

    # divやsectionなどの構造も確認
    print("=== その他の構造 ===")
    divs_with_ranking = soup.find_all("div", class_=lambda x: x and "ranking" in x.lower())
    print(f"'ranking'を含むdiv: {len(divs_with_ranking)}個")

    # ページタイトルを確認
    title = soup.find("title")
    if title:
        print(f"ページタイトル: {title.get_text(strip=True)}")

    # meta情報を確認
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        print(f"ページ説明: {meta_desc.get('content', '')[:100]}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "morning"
    inspect_html_structure(target)
