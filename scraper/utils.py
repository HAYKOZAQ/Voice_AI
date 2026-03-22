from playwright.sync_api import Locator
import logging

logger = logging.getLogger("scraper.utils")

def extract_tables_as_json(locator: Locator) -> list:
    """
    Extracts all <table> elements within a given Playwright locator 
    and converts them into a list of list of dictionaries (rows mapped to headers).
    """
    tables_data = []
    tables = locator.locator("table").all()
    
    for table in tables:
        try:
            if not table.is_visible():
                continue
                
            rows = table.locator("tr").all()
            if len(rows) < 2:
                continue
                
            # Attempt to extract headers from the first row
            th_elements = rows[0].locator("th").all()
            if not th_elements:
                # If no <th> exist, assume the first row's <td> are headers
                th_elements = rows[0].locator("td").all()
                
            headers = [th.inner_text().strip().replace('\n', ' ') for th in th_elements]
            
            # Fallback if headers are empty
            if not headers or all(h == "" for h in headers):
                headers = [f"Column_{i}" for i in range(len(th_elements))]
            
            table_rows = []
            for row in rows[1:]:
                cells = row.locator("td").all()
                if not cells:
                    continue
                    
                row_data = {}
                for i, cell in enumerate(cells):
                    header = headers[i] if i < len(headers) else f"Column_{i}"
                    val = cell.inner_text().strip().replace('\n', ' ')
                    if val:  # Only keep non-empty cells
                        row_data[header] = val
                
                if row_data:
                    table_rows.append(row_data)
                    
            if table_rows:
                tables_data.append(table_rows)
                
        except Exception as e:
            logger.warning(f"Failed to parse a table: {e}")
            continue
            
    return tables_data
