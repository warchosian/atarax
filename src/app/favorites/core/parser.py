from bs4 import BeautifulSoup
from typing import Dict, List, Union

def parse_favorites_html(file_path: str) -> Dict:
    """
    Parses a Chrome favorites HTML file and extracts its hierarchical structure.

    Args:
        file_path: The path to the Chrome favorites HTML file.

    Returns:
        A dictionary representing the hierarchical structure of the favorites.
        Each key is a folder name or 'Bookmarks Bar'/'Other Bookmarks',
        and its value is a list of items (subfolders or bookmarks).
        Bookmarks are represented as dictionaries with 'name' and 'url'.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')

    # Let's refine with a recursive approach
    def extract_items(parent_dl) -> List[Dict]:
        items = []
        
        for child in parent_dl.children:
            if child.name == 'dt':
                h3_tag = child.find('h3')
                a_tag = child.find('a')

                if h3_tag: # It's a folder
                    folder_name = h3_tag.get_text().strip()
                    folder_content = []
                    # Find the immediate next DL tag which contains children of this folder
                    next_dl_sibling = child.find_next_sibling('dl')
                    if next_dl_sibling:
                        folder_content.extend(extract_items(next_dl_sibling))
                    items.append({folder_name: folder_content})
                elif a_tag: # It's a bookmark
                    bookmark_name = a_tag.get_text().strip()
                    bookmark_url = a_tag.get('href')
                    if bookmark_name and bookmark_url:
                        items.append({'name': bookmark_name, 'url': bookmark_url})
            elif child.name == 'p':
                # Ignore paragraphs, they are often descriptions for folders
                pass
            # Other DL tags encountered here that are not direct children of DT are handled by recursion

        return items

    # Try to find the root DL that contains all bookmarks
    # A common structure for Chrome bookmarks starts with <body> then <DL>
    root_dl = soup.find('body').find('dl', recursive=False) # Only direct child DL of body
    if not root_dl:
        # Fallback to just the first DL if direct child of body is not found
        root_dl = soup.find('dl', recursive=False)
    
    if root_dl:
        hierarchy = {"Bookmarks": extract_items(root_dl)}
    else:
        hierarchy = {"Bookmarks": []}

    return hierarchy
