from PIL import Image, ImageOps, ImageDraw
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pandas as pd
import matplotlib.pyplot as plt
import os


# Load and clean CSV
df = pd.read_csv('sp500.csv')
df.columns = df.columns.str.strip()
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
df = df.sort_values('Date').reset_index(drop=True)

# Column with price data
price_col = 'Close'

# Inauguration dates
inaugurations = {
    "George W. Bush": ("2001-01-20", "bush.png", "red"),
    "Barack Obama": ("2009-01-20", "obama.png", "blue"),
    "Donald Trump": ("2017-01-20", "trump.png", "red"),
    "Joe Biden": ("2021-01-20", "biden.png", "blue"),
    "Donald Trump (2nd Term)": ("2025-01-20", "trump2.png", "red")
}

# Today's date
today = pd.to_datetime("2025-04-02")

# Set up plot
fig, ax = plt.subplots(figsize=(12, 7))

# Function to crop image to circle with transparent background
def circular_crop_with_border(image_path, size=40, border_size=3, border_color="red"):
    img = Image.open(image_path).convert("RGBA")
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    
    # Create mask
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    
    # Add border
    bordered_size = size + border_size * 2
    border_img = Image.new("RGBA", (bordered_size, bordered_size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.ellipse((0, 0, bordered_size, bordered_size), fill=border_color)
    border_img.paste(img, (border_size, border_size), img)
    
    return border_img



# Loop through presidents
for president, (date, img_file, party_color) in inaugurations.items():
    start_date = pd.to_datetime(date)
    try:
        start_row = df[df['Date'] >= start_date].iloc[0]
        start_index = df[df['Date'] == start_row['Date']].index[0]

        future_df = df.iloc[start_index:]
        max_days = min(200, (future_df[future_df['Date'] <= today]).shape[0])
        if max_days < 5:
            print(f"Not enough data for {president}")
            continue

        window = df.iloc[start_index:start_index + max_days]
        start_price = window.iloc[0][price_col]
        gains = (window[price_col] - start_price) / start_price * 100
        gains = gains.reset_index(drop=True)

        # Plot line
        ax.plot(gains, label=president, linewidth=2)

        # Add image at end of line
        image_path = os.path.join("images", img_file)
        if os.path.exists(image_path):
            last_x = len(gains) - 1
            last_y = gains.iloc[-1]

            cropped_img = circular_crop_with_border(image_path, border_color=party_color)
            im = OffsetImage(cropped_img, zoom=0.6)  # Try 0.6 or 0.7
            ab = AnnotationBbox(im, (last_x, last_y), frameon=False, pad=0.2)
            ax.add_artist(ab)
        else:
            print(f"Image not found: {image_path}")


    except Exception as e:
        print(f"Error for {president}: {e}")

ax.set_title("S&P 500 % Gain in First 200 Trading Days of Each Presidency", fontsize=14)
ax.set_xlabel("Trading Days Since Inauguration")
ax.set_ylabel("Cumulative % Gain")
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.show()
