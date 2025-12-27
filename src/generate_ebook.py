#!/usr/bin/env python3

import shutil
import logging
import shlex
import subprocess
import os
import re
import zipfile

from string import Template

import yaml

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.realpath(f"{SCRIPT_PATH}/..")
METADATA_PATH = os.path.join(SCRIPT_PATH, "../inputs/metadata.yaml")
EPUB_TEMPLATE_PATH = os.path.join(SCRIPT_PATH, "../epub-template")
OUTPUT_PATH = os.path.join(SCRIPT_PATH, "../out_epub")


def get_metadata():
    """Gets the metadata from disk."""
    with open(METADATA_PATH, mode="rt", encoding="utf-8") as file_handle:
        return yaml.safe_load(file_handle)


def real_join(a, *p):
    return os.path.realpath(os.path.join(a, *p))


def generate_file(filename, **mapping):
    in_path = real_join(EPUB_TEMPLATE_PATH, filename)
    out_path = real_join(OUTPUT_PATH, filename)
    with open(in_path, "r", encoding="utf-8") as f:
        file_tmpl = Template(f.read())
    file_contents = file_tmpl.substitute(**mapping)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(file_contents)
    print(f"Wrote {out_path.replace(PROJECT_PATH, '.')}")


def generate_cover_jpg(metadata):
    # rsvg-convert can only generate PNGs, but tools which can do direct SVG -> JPG
    # conversion do not support all SVG features we need.
    svg_path = real_join(OUTPUT_PATH, "cover.svg")
    png_path = real_join(OUTPUT_PATH, "cover.png")
    jpg_path = real_join(OUTPUT_PATH, "cover.jpg")
    cmd_args = shlex.split(
        f"rsvg-convert -h 1500 -w 938 --format png --output {png_path} {svg_path}"
    )
    subprocess.run(cmd_args)
    subprocess.run(shlex.split(f"magick {png_path} {jpg_path}"))
    os.remove(svg_path)
    os.remove(png_path)
    print(f"Wrote {jpg_path.replace(PROJECT_PATH, '.')}")


def parse_book_contents(metadata):
    content_path = real_join(SCRIPT_PATH, "../inputs/content.html")
    with open(content_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on the <p>chapter</p> marker
    # This will give chunks of text between those markers
    chapter_parts = re.split(
        r"<p>?\s*(?:<strong>)?\s*chapter\s*(?:</strong>)?\s*</p>",
        content,
        flags=re.IGNORECASE,
    )

    filename = "chapter-template.xhtml"
    in_path = real_join(EPUB_TEMPLATE_PATH, filename)
    real_chapters = 0

    for chapter_content in chapter_parts:
        chapter_content = chapter_content.replace("&nbsp;", chr(0x00A0))
        chapter_content = re.sub(
            r"<p><em>\s*</em>\s*\*</p>",
            '<p class="section-break">*</p>',
            chapter_content,
        )
        if len(chapter_content.strip()) == 0:
            continue
        real_chapters += 1
        with open(in_path, "r", encoding="utf-8") as f:
            chapter_tmpl = Template(f.read())
        out_str = chapter_tmpl.substitute(
            **metadata,
            chapter_number_padded=f"{real_chapters:03}",
            chapter_number=real_chapters,
            chapter_content=chapter_content,
        )
        out_path = real_join(OUTPUT_PATH, f"chapter-{real_chapters:03}.xhtml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"Wrote {out_path.replace(PROJECT_PATH, '.')}")
    return real_chapters


def generate_metadata_opf(metadata, chapter_count):
    filename = "metadata.opf"
    in_path = real_join(EPUB_TEMPLATE_PATH, filename)
    out_path = real_join(OUTPUT_PATH, filename)
    with open(in_path, "r", encoding="utf-8") as f:
        input_tmpl = Template(f.read())
    chapter_item_list = ""
    chapter_itemref_list = ""
    for i in range(1, chapter_count + 1):
        chapter_item_list += f'    <item id="chapter-{i:03}-xhtml" href="chapter-{i:03}.xhtml" media-type="application/xhtml+xml"/>\n'
        chapter_itemref_list += f'    <itemref idref="chapter-{i:03}-xhtml"/>\n'
    out_str = input_tmpl.substitute(
        **metadata,
        chapter_item_list=chapter_item_list.strip(),
        chapter_itemref_list=chapter_itemref_list.strip(),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_str)
    print(f"Wrote {out_path.replace(PROJECT_PATH, '.')}")


def generate_page_toc(metadata, chapter_count):
    filename = "page-toc.xhtml"
    in_path = real_join(EPUB_TEMPLATE_PATH, filename)
    out_path = real_join(OUTPUT_PATH, filename)
    with open(in_path, "r", encoding="utf-8") as f:
        input_tmpl = Template(f.read())
    toc_chapters = ""
    for i in range(1, chapter_count + 1):
        toc_chapters += (
            f'      <li><a href="chapter-{i:03}.xhtml">Chapter {i}</a></li>\n'
        )
    out_str = input_tmpl.substitute(
        language_code=metadata["language_code"],
        toc_chapters=toc_chapters.strip(),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_str)
    print(f"Wrote {out_path.replace(PROJECT_PATH, '.')}")


def generate_toc_ncx(metadata, chapter_count):
    filename = "toc.ncx"
    in_path = real_join(EPUB_TEMPLATE_PATH, filename)
    out_path = real_join(OUTPUT_PATH, filename)
    with open(in_path, "r", encoding="utf-8") as f:
        input_tmpl = Template(f.read())
    chapter_navpoints = ""
    playOrderIdx = 4
    for i in range(1, chapter_count + 1):
        chapter_navpoints += f"""    <navPoint id="np-{i:03}" playOrder="{playOrderIdx}">
      <navLabel>
        <text>Chapter {i}</text>
      </navLabel>
      <content src="chapter-{i:03}.xhtml" />
    </navPoint>\n"""
        playOrderIdx += 1
    out_str = input_tmpl.substitute(
        **metadata,
        chapter_navpoints=chapter_navpoints.strip(),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_str)
    print(f"Wrote {out_path.replace(PROJECT_PATH, '.')}")


def create_the_ebook():
    zip_path = real_join(SCRIPT_PATH, "../book.epub")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUTPUT_PATH):
            for file in files:
                file_path = os.path.join(root, file)
                # Store relative path inside the zip
                arcname = os.path.relpath(file_path, start=OUTPUT_PATH)
                zipf.write(file_path, arcname)
    print(f"Wrote {zip_path.replace(PROJECT_PATH, '.')}")


def main():
    """Main app execution code."""
    metadata = get_metadata()

    if os.path.isdir(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
    shutil.copytree(
        EPUB_TEMPLATE_PATH,
        OUTPUT_PATH,
        dirs_exist_ok=True,
        copy_function=shutil.copy,
    )
    os.remove(os.path.join(OUTPUT_PATH, "chapter-template.xhtml"))

    generate_file("cover.svg", **metadata)
    generate_cover_jpg(metadata)
    generate_file("page-cover.xhtml", **metadata)
    generate_file("page-title.xhtml", **metadata)
    generate_file("page-copyright.xhtml", **metadata)
    chapter_count = parse_book_contents(metadata)
    generate_metadata_opf(metadata, chapter_count)
    generate_page_toc(metadata, chapter_count)
    generate_toc_ncx(metadata, chapter_count)

    create_the_ebook()


if __name__ == "__main__":
    main()
