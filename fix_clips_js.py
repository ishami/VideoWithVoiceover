#!/usr/bin/env python3

with open('static/js/clips.js', 'r') as f:
    content = f.read()

# Fix the element selectors
content = content.replace("const mediaBody = $('#mediaBody');", "const clipBody = $('#clipBody');")
content = content.replace("const musicBody = $('#musicBody');", "// const musicBody = $('#musicBody'); // Not used - single table")

# Fix the Sortable initialization
content = content.replace("if (mediaBody && typeof Sortable !== 'undefined') {", "if (clipBody && typeof Sortable !== 'undefined') {")
content = content.replace("console.log('Initializing media sortable');", "console.log('Initializing clips sortable');")
content = content.replace("new Sortable(mediaBody, {", "new Sortable(clipBody, {")

# Remove the music sortable since we have a single table
content = content.replace("""if (musicBody && typeof Sortable !== 'undefined') {
      console.log('Initializing music sortable');
      new Sortable(musicBody, {
        animation: 150,
        ghostClass: 'bg-light',
        onEnd: evt => {
          console.log('Music reordered:', evt.oldIndex, '→', evt.newIndex);
          saveOrder();
        }
      });
    }""", "// Music sortable not needed - single table structure")

# Fix the saveOrder function to work with single table
old_save_order = """function saveOrder() {
      const mediaOrder = $$('#mediaBody tr').map((tr, i) => ({
        id: +tr.dataset.id,
        pos: i + 1
      }));
      const musicOrder = $$('#musicBody tr').map((tr, i) => ({
        id: +tr.dataset.id,
        pos: i + 1
      }));"""

new_save_order = """function saveOrder() {
      const rows = $$('#clipBody tr').filter(tr => tr.dataset.id);
      const mediaOrder = rows.map((tr, i) => ({
        id: +tr.dataset.id,
        pos: i + 1
      }));
      const musicOrder = []; // Not separate in this layout"""

content = content.replace(old_save_order, new_save_order)

# Fix delete function selectors
content = content.replace('const row = $(`#mediaBody tr[data-id="${id}"]`);', 'const row = $(`#clipBody tr[data-id="${id}"]`);')
content = content.replace('const row = $(`#musicBody tr[data-id="${id}"]`);', '// Music rows are in same table')

# Fix the debug log at the end
content = content.replace("mediaClips: $$('#mediaBody tr').length,", "mediaClips: $$('#clipBody tr').length,")
content = content.replace("musicClips: $$('#musicBody tr').length,", "musicClips: $$('#clipBody tr').length, // same table")

with open('static/js/clips.js', 'w') as f:
    f.write(content)

print("Fixed clips.js selectors")
