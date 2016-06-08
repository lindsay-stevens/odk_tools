# http://stackoverflow.com/a/26304106
find ./ -iname "*.md" -type f -exec sh -lc 'pandoc "${0}" -o "${0%.md}.docx"' {} \;