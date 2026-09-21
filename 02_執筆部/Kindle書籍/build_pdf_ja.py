#!/usr/bin/env python3
"""
ペーパーバック PDF ビルドスクリプト
Kindle Publisher スキル用

Usage:
  python3 build_pdf.py --title "タイトル" --author "著者名" --content manuscript.md --output book.pdf
"""

import argparse
import os
import re
import sys


def install_if_needed():
    """必要なライブラリを確認・インストール"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import inch
        from reportlab.pdfbase import pdfmetrics
        return True
    except ImportError:
        print("reportlabをインストールしています...")
        os.system(f"{sys.executable} -m pip install reportlab --break-system-packages -q")
        return True


def parse_markdown_for_pdf(md_text):
    """MarkdownをPDF用のブロック構造に変換"""
    blocks = []
    for line in md_text.split('\n'):
        if line.startswith('# '):
            blocks.append({'type': 'h1', 'text': line[2:].strip()})
        elif line.startswith('## '):
            blocks.append({'type': 'h2', 'text': line[3:].strip()})
        elif line.startswith('### '):
            blocks.append({'type': 'h3', 'text': line[4:].strip()})
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({'type': 'bullet', 'text': line[2:].strip()})
        elif re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line)
            blocks.append({'type': 'numbered', 'text': text.strip()})
        elif line.strip() == '':
            blocks.append({'type': 'empty', 'text': ''})
        else:
            # 太字マークダウンを除去（シンプル化）
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            blocks.append({'type': 'paragraph', 'text': text.strip()})
    return blocks


def build_pdf(title, author, content_file, output_file, page_size='6x9'):
    """ペーパーバック用PDFをビルドする"""

    install_if_needed()

    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.platypus import ListFlowable, ListItem
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

    # ページサイズ設定
    sizes = {
        '6x9': (6 * inch, 9 * inch),
        '5x8': (5 * inch, 8 * inch),
        '5.5x8.5': (5.5 * inch, 8.5 * inch),
    }
    page_w, page_h = sizes.get(page_size, sizes['6x9'])

    # マージン設定
    margin_top = 1.5 * cm
    margin_bottom = 1.5 * cm
    margin_outer = 1.5 * cm
    margin_inner = 1.8 * cm

    # Markdownを読み込む
    with open(content_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    blocks = parse_markdown_for_pdf(md_text)

    # フォントを試みる（日本語フォント）
    font_name = 'Helvetica'  # フォールバック
    try:
        # システムのNoto Sans JPを探す
        font_paths = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
            '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                pdfmetrics.registerFont(TTFont('NotoSansJP', fp))
                font_name = 'NotoSansJP'
                print(f"✅ 日本語フォント読み込み成功：{fp}")
                break
    except Exception as e:
        print(f"⚠️ 日本語フォントの読み込みに失敗しました。英数字のみ正常に表示されます。: {e}")

    # スタイル定義
    styles = {
        'h1': ParagraphStyle(
            'H1', fontName=font_name, fontSize=18, leading=24,
            spaceBefore=24, spaceAfter=12, textColor=colors.HexColor('#1a1a1a'),
            borderPadding=(0, 0, 6, 0)
        ),
        'h2': ParagraphStyle(
            'H2', fontName=font_name, fontSize=14, leading=20,
            spaceBefore=18, spaceAfter=8, textColor=colors.HexColor('#2a2a2a'),
        ),
        'h3': ParagraphStyle(
            'H3', fontName=font_name, fontSize=12, leading=18,
            spaceBefore=14, spaceAfter=6, textColor=colors.HexColor('#3a3a3a'),
        ),
        'body': ParagraphStyle(
            'Body', fontName=font_name, fontSize=10.5, leading=18,
            spaceBefore=0, spaceAfter=6, alignment=TA_JUSTIFY,
            firstLineIndent=10
        ),
        'bullet': ParagraphStyle(
            'Bullet', fontName=font_name, fontSize=10.5, leading=18,
            spaceBefore=2, spaceAfter=2, leftIndent=20, bulletIndent=10
        ),
    }

    # PDFドキュメント作成
    doc = SimpleDocTemplate(
        output_file,
        pagesize=(page_w, page_h),
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        leftMargin=margin_inner,
        rightMargin=margin_outer,
        title=title,
        author=author,
    )

    story = []
    page_num = [1]

    # タイトルページ
    story.append(Spacer(1, 2 * inch))
    title_style = ParagraphStyle(
        'Title', fontName=font_name, fontSize=24, leading=36,
        alignment=TA_CENTER, textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=24
    )
    author_style = ParagraphStyle(
        'Author', fontName=font_name, fontSize=14, leading=20,
        alignment=TA_CENTER, textColor=colors.HexColor('#555555'),
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(author, author_style))
    story.append(PageBreak())

    # 本文
    bullet_counter = 1
    for block in blocks:
        if block['type'] == 'h1':
            story.append(Paragraph(block['text'], styles['h1']))
        elif block['type'] == 'h2':
            story.append(Paragraph(block['text'], styles['h2']))
        elif block['type'] == 'h3':
            story.append(Paragraph(block['text'], styles['h3']))
        elif block['type'] == 'paragraph':
            if block['text']:
                story.append(Paragraph(block['text'], styles['body']))
        elif block['type'] == 'bullet':
            story.append(Paragraph(f'• {block["text"]}', styles['bullet']))
        elif block['type'] == 'numbered':
            story.append(Paragraph(f'{bullet_counter}. {block["text"]}', styles['bullet']))
            bullet_counter += 1
        elif block['type'] == 'empty':
            story.append(Spacer(1, 6))
            bullet_counter = 1

    # PDF生成
    doc.build(story)

    print(f"✅ ペーパーバックPDFを生成しました：{output_file}")
    print(f"   ページサイズ：{page_size}インチ")
    print(f"   ファイルサイズ：{os.path.getsize(output_file):,} bytes")
    print(f"   💡 KDP Previewerで確認後、アップロードしてください")


def main():
    parser = argparse.ArgumentParser(description='Kindle ペーパーバック PDF ビルドスクリプト')
    parser.add_argument('--title', required=True, help='本のタイトル')
    parser.add_argument('--author', required=True, help='著者名')
    parser.add_argument('--content', required=True, help='原稿Markdownファイルのパス')
    parser.add_argument('--page-size', default='6x9', choices=['6x9', '5x8', '5.5x8.5'],
                        help='ページサイズ（デフォルト：6x9）')
    parser.add_argument('--output', required=True, help='出力PDFファイル名')

    args = parser.parse_args()

    if not os.path.exists(args.content):
        print(f"❌ エラー：原稿ファイルが見つかりません：{args.content}")
        return

    build_pdf(
        title=args.title,
        author=args.author,
        content_file=args.content,
        output_file=args.output,
        page_size=args.page_size
    )


if __name__ == '__main__':
    main()
