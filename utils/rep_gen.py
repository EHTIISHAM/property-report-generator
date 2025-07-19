from fpdf import FPDF
import re
import requests
import os
from PIL import Image
import random

def format_address(address):
    address = re.sub(r"[ ,]+", "_", address)   # Replace spaces and commas with underscores
    address = address.replace("#", "_HASH_")        # Replace '#' with '-' or another safe character
    return address

def download_image(image_url: str, save_dir: str = "downloads", filename: str = None) -> str:
    os.makedirs(save_dir, exist_ok=True)
    if not filename:
        filename = os.path.basename(image_url.split("?")[0])
    file_path = os.path.join(save_dir, filename)

    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")
        return ""

def process_image(image_path: str, output_dir: str = "downloads") -> str:
    try:
        os.makedirs(output_dir, exist_ok=True)
        with Image.open(image_path) as img:
            img.load()
        os.remove(image_path)
        resized_img = img.resize((1280, 720))
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        if resized_img.mode != 'RGB':
            resized_img = resized_img.convert('RGB')
        new_image_path = os.path.join(output_dir, f"{base_name}_resized.jpg")
        resized_img.save(new_image_path, format="JPEG")
        return new_image_path
    except Exception as e:
        print(f"Error processing image: {e}")
        return ""

def sanitize_text(text):
    if text:
        replacements = {"\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2014": '-', "\u2013": '-'}
        for key, val in replacements.items():
            text = text.replace(key, val)
        return text.encode('latin-1', 'ignore').decode('latin-1')
    return ""

def parse_comparables(data,avg):
    prices = []
    square_footages = []
    lot_sizes = []
    years_built = []
    buyer_preferences = []

    for entry in data:
        # Extract sale price
        price_match = re.search(r"Sale Price: \$(\d+(\.\d{2})?)", entry)
        if price_match:
            prices.append(float(price_match.group(1)))

        # Extract square footage
        sq_ft_match = re.search(r"Square Footage: (\d+(\.\d+)?) sq ft", entry)
        if sq_ft_match:
            sq_ft_match = sq_ft_match.group(1).replace(",","").replace(".00","")
            square_footages.append(int(sq_ft_match))

        # Extract lot size
        lot_size_match = re.search(r"Lot Size: (\d+(\.\d+)?) sq ft", entry)
        if lot_size_match:
            lot_sizes.append(float(lot_size_match.group(1)))

        # Extract year built
        year_built_match = re.search(r"Year Built: (\d+)", entry)
        if year_built_match:
            years_built.append(int(year_built_match.group(1)))

    # Calculate averages
    avg_price = sum(prices) / len(prices) if prices else 0
    avg_sq_ft = sum(square_footages) / len(square_footages) if square_footages else 0
    avg_lot_size = sum(lot_sizes) / len(lot_sizes) if lot_sizes else 0
    avg_year_built = sum(years_built) / len(years_built) if years_built else 0

    # Generate insights
    pricing_trends = (
        f"Pricing Trends: The average price of comparable homes is approximately {avg}. "
        f"Homes typically have an average size of {avg_sq_ft:.0f} sq ft and a lot size of {avg_lot_size:.0f} sq ft."
    )
    preferences_summary = (
        f"Buyer Preferences: Buyers tend to prefer homes built around {avg_year_built:.0f} "
        f"with spacious lots averaging {avg_lot_size:.0f} sq ft."
    )

    return preferences_summary, pricing_trends

class ReportPDF(FPDF):
    def header(self):
        pass

    def section_title(self, title, size_font=12, align='L'):
        self.set_font('Helvetica', 'B', size_font)
        self.cell(0, 10, title, ln=1, align=align)
        self.ln(2)

    def section_body(self, text):
        self.set_font('Helvetica', '', 10)
        self.multi_cell(0, 10, text)
        self.ln()

    def add_photo(self, photo_path, y=None, w=50):
        img = Image.open(photo_path)
        aspect_ratio = img.height / img.width
        h = w * aspect_ratio
        if y is None:
            y = self.get_y()
        if y + h > self.h - self.b_margin:
            self.add_page()
            y = self.t_margin
        x = (self.w - w) / 2
        self.image(photo_path, x=x, y=y, w=w, h=h)
        self.set_y(y + h + 5)

    def add_horizontal_line(self, y_position=None, line_width=0.5):
        if y_position is None:
            y_position = self.get_y() + 5
        self.set_line_width(line_width)
        page_width = self.w - 2 * self.l_margin
        self.line(self.l_margin, y_position, self.l_margin + page_width, y_position)
        self.ln(10)

    def add_photo_grid(self, photo_path, y=None, w=200):
        # Open the image to get its original dimensions
        img = Image.open(photo_path)
        img_width, img_height = img.size  

        # Maintain the original aspect ratio
        aspect_ratio = img_height / img_width  
        h = w * aspect_ratio  # Calculate height based on width

        # Ensure y is set correctly
        if y is None:
            y = self.get_y()
            if y < self.t_margin:
                y = self.t_margin

        # Check if the image fits on the current page
        if y + h > self.h - self.b_margin:  
            self.add_page()  # Add a new page if image doesn't fit
            y = self.t_margin  # Reset y to top margin

        # Set the X position (Aligning to left)
        x = (self.w - w) / 2

        # Add the image
        self.image(photo_path, x=x, y=y, w=w, h=h)  

        # Update y position for subsequent content
        self.set_y(y + h + 5)  

    def add_clickable_link(self, text, url, font_size=12):
        """
        Add a clickable link to the PDF, center-aligned.

        Args:
        - text (str): The display text for the link.
        - url (str): The URL that should be clickable.
        - font_size (int): Font size for the link text (default is 12).
        """
        self.set_font('Arial', 'U', font_size)  # Underline to make it look like a link
        self.set_text_color(0, 0, 255)  # Blue color for the link
        
        # Calculate page width and center the link
        page_width = self.w
        text_width = self.get_string_width(text) + 6  # Small padding for spacing
        x_position = (page_width - text_width) / 2

        # Set X position for centering and add the clickable link
        self.set_x(x_position)
        self.cell(text_width, 10, text, ln=True, link=url, align='C')

        # Reset text color
        self.set_text_color(0, 0, 0)
    def add_property(self, image_path, text, link_text, link_url):
        # Configure styling
        self.set_font("Arial", size=12)
        line_height = self.font_size * 1.2
        element_spacing = 4
        img_width = 70
        
        # Calculate image height
        self.ln(4)
        img = Image.open(image_path)
        aspect_ratio = img.height / img.width
        img_height = img_width * aspect_ratio
        
        # Calculate table dimensions
        table_width = 150  # Total width of details box
        label_width = 60   # Width for labels column
        value_width = table_width - label_width
        
        # Split and clean text
        details = [line.strip().lstrip('- ') for line in text.split('\n') if line.strip()]
        
        # Calculate required height
        text_height = 0
        for line in details:
            if ':' in line:
                label, value = line.split(':', 1)
                value_lines = max(1, self.get_string_width(value.strip()) // value_width + 1)
                text_height += line_height * value_lines
            else:
                text_height += line_height
        
        total_height = img_height + text_height + (len(details)*2) + line_height + 20
        
        # Page break check
        if self.get_y() + total_height > self.h - self.b_margin:
            self.add_page()
        
        # Centered image
        self.image(image_path, x=(self.w - img_width)/2, w=img_width)
        self.ln(element_spacing)
        x_start = (self.w - table_width) / 2  # Center calculation

        # Centered clickable link
        self.ln(element_spacing)
        self.set_x(x_start)
        self.set_text_color(0, 0, 255)
        self.set_font("Arial", 'U', 12)
        link_width = self.get_string_width(link_text)
        self.cell(table_width, line_height, link_text, align='C', link=link_url)
        self.set_text_color(0, 0, 0)
        self.ln(10)
        # Centered property details table
        x_start = (self.w - table_width) / 2  # Center calculation
        self.set_x(x_start)
        
        # Table header
        self.set_font("Arial", 'B', 14)
        self.cell(table_width, line_height*1.5, "Property Details", border=1, ln=1, align='C')
        self.set_font("Arial", '', 12)
        
        # Table rows with dynamic wrapping
        for line in details:
            self.set_x(x_start)  # Maintain centered position
            if ':' in line:
                label, value = line.split(':', 1)
                label = label.strip() + ":"
                value = value.strip()
                
                # Label cell
                self.set_font("Arial", 'B', 12)
                self.cell(label_width, line_height, label, border='LTR')
                
                # Value cell with wrapping
                self.set_font("Arial", '', 12)
                self.multi_cell(value_width, line_height, value, border='LTR')
            else:
                self.multi_cell(table_width, line_height, line, border=1)
        

def generate_report_seller(main_data,mainprop_url,estimated_value,comparable_data,photo_links,source_link_past,current_data,phoyo_links_current,source_link_current,tag,recommendation,additional_consideration,output_path):
    # MAIN address
    address_main_property = main_data.split("\n")[0].split(":")[1].strip()
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_photo("utils/Transparent file SOUH -01 copy.png")  # company logo
    pdf.section_title("Home Pricing Report For",size_font=16,align='C')
    pdf.section_title(address_main_property,size_font=14,align='C')
    pdf.add_horizontal_line()
    # Property Overview
    pdf.section_title("Property Overview",align='C')
   
    try:
        path_pic = download_image(mainprop_url)
        path_pic = process_image(path_pic)
        pdf.add_photo(path_pic)  # Replace with actual image path
        os.remove(path_pic)
    except:
        path_pic = "const1.jpg"
        pdf.add_photo(path_pic)     
    pdf.section_body(main_data)
    pdf.add_horizontal_line()
    # Comparable Properties (Last 6 Months)
    pdf.section_title("Comparable Properties (Last 6 Months)")
    pdf.add_photo_grid("utils/past_sales.jpg")

    if len(comparable_data) == 0:
        pdf.section_body("No comparable properties found in the last 6 months.")
    else:
        print(len(comparable_data),len(photo_links),len(source_link_past))
        for i in range(len(comparable_data)):
            path_pic = download_image(photo_links[i])
            path_pic = process_image(path_pic)
            pdf.add_property(path_pic, comparable_data[i], "View Listing", source_link_past[i])
            
            os.remove(path_pic)

    pdf.add_horizontal_line()
    # Add more properties similarly...
    pdf.section_title("Comparable Properties Currently on the Market ")
    pdf.add_photo_grid("utils/on_market.jpg")

    if len(current_data) == 0:
        pdf.section_body("No comparable properties found")
    else:
        print(len(current_data),len(phoyo_links_current),len(source_link_current))
        for i in range(len(current_data)):
            path_pic = download_image(phoyo_links_current[i])
            path_pic = process_image(path_pic)
            pdf.add_property(path_pic, current_data[i], "View Listing", source_link_current[i])
            os.remove(path_pic)
    pdf.add_horizontal_line()

    pdf.section_title("Recommended Pricing Strategy",size_font=14)
    pdf.section_body(sanitize_text(recommendation))

    # Additional Considerations
    pdf.add_horizontal_line()
    pdf.section_title("Additional Considerations",size_font=14)
    pdf.section_body(sanitize_text(additional_consideration))

    # Disclaimer
    pdf.add_horizontal_line()
    pdf.section_title("Disclaimer")
    pdf.section_body("This report is based on publicly available data and market trends. It is intended for informational purposes only and does not constitute professional real estate advice. Buyers should consult a licensed real estate attorney or professional for specific guidance.")
    pdf.add_horizontal_line()
    pdf.section_title("Ready to Sell?",size_font=14)
    pdf.section_body("List your home for FREE on www.SaveOnYourHome.com and explore the tools and guidance we provide to make your selling experience as efficient and successful as possible.")
    pdf.add_photo("utils/Transparent file character -01-01.png")
    # Output the PDF
    pdf.output(output_path+f"seller_report{format_address(address_main_property)}.pdf")
    print(f"Report saved to {output_path}")
    return output_path+f"seller_report{sanitize_text(format_address(address_main_property))}.pdf"


def generate_buyer_report(main_data,img_url,estimated_value,comparable_data,photo_links,source_link_past,current_data,photo_links_current,source_link_current,tag,recommendation,additional_consideration,output_path):
    address_main_property = main_data.split("\n")[0].split(":")[1].strip()
    pdf = ReportPDF()
    pdf.add_page()
    pdf.add_photo("utils/Transparent file SOUH -01 copy.png")  # company logo
    pdf.section_title("Home Pricing Report For",size_font=16,align='C')
    pdf.section_title(address_main_property,size_font=14,align='C')
    pdf.add_horizontal_line()
    pdf.section_title("Property Overview",align='C')
    try:
        path_pic = download_image(img_url)
        path_pic = process_image(path_pic)
        pdf.add_photo(path_pic)  # Replace with actual image path
        os.remove(path_pic)
    except:
        path_pic = "const1.jpg"
        pdf.add_photo(path_pic)  
    pdf.section_body(main_data)

    pdf.add_horizontal_line()
    city_state = address_main_property.split(",")[1].strip()  # Extract city and state part
    city_name = " ".join(city_state.split()[:2])  # Get the first two words (city name)
    pdf.section_title(f"Current Market Trends in {city_name}", size_font=14, align='L')
    preferences_summary, pricing_trends = parse_comparables(comparable_data,estimated_value[1])
    pdf.section_body(preferences_summary)
    pdf.section_body(pricing_trends)
    pdf.add_horizontal_line()
    pdf.section_title("Comparable Properties (Last 6 Months)")
    pdf.add_photo_grid("utils/past_sales.jpg")

    if len(comparable_data) == 0:
        pdf.section_body("No comparable properties found in the last 6 months.")
    else:
        for i in range(len(comparable_data)):
            path_pic = download_image(photo_links[i])
            path_pic = process_image(path_pic)

            pdf.add_property(path_pic, comparable_data[i], "View Listing", source_link_past[i])
            os.remove(path_pic)
    pdf.add_horizontal_line()
    pdf.section_title("Comparable Properties Currently on the Market ")
    pdf.add_photo_grid("utils/on_market.jpg")
    if len(current_data) == 0:
        pdf.section_body("No comparable properties found")
    else:
        for i in range(len(current_data)):
            path_pic = download_image(photo_links_current[i])
            path_pic = process_image(path_pic)
            pdf.add_property(path_pic, current_data[i], "View Listing", source_link_current[i])
            os.remove(path_pic)
    pdf.add_horizontal_line()
    pdf.section_title("Suggested Offer Pricing Strategy",size_font=14)
    pdf.section_body(sanitize_text(recommendation))
    pdf.add_horizontal_line()
    # Additional Considerations
    pdf.section_title("Additional Considerations",size_font=14)
    pdf.section_body(sanitize_text(additional_consideration))

    pdf.add_horizontal_line()
    # Disclaimer
    pdf.section_title("Disclaimer")
    pdf.section_body("This report is based on publicly available data and market trends. It is intended for informational purposes only and does not constitute professional real estate advice. Buyers should consult a licensed real estate attorney or professional for specific guidance.")
    pdf.add_horizontal_line()
    pdf.section_title("Ready to Explore More Options?")
    pdf.section_body("""Visit www.SaveOnYourHome.com for additional tools and guidance to help you confidently navigate the home-buying process.""")
    pdf.add_photo("utils/Transparent file character -01-01.png")
    # Output the PDF
    pdf.output(output_path+f"buyer_report{format_address(address_main_property)}.pdf")
    print(f"Report saved to {output_path}")
    return output_path+f"buyer_report{sanitize_text(format_address(address_main_property))}.pdf"
