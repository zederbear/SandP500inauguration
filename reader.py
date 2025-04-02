import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Circle
from PIL import Image, ImageOps, ImageDraw
import os

# === SETTINGS === #
CSV_PATH = 'sp500.csv'
IMAGE_DIR = 'images'
PRICE_COLUMN = 'Close'
TODAY = pd.to_datetime("2025-04-02")

# === PRESIDENT DATA === #
inaugurations = {
    "George W. Bush": ("2001-01-20", "bush.png", "red"),
    "Barack Obama": ("2009-01-20", "obama.png", "blue"),
    "Donald Trump": ("2017-01-20", "trump.png", "red"),
    "Joe Biden": ("2021-01-20", "biden.png", "blue"),
    "Donald Trump (2nd Term)": ("2025-01-20", "trump2.png", "red")
}

# === HELPERS === #
def circular_crop_with_border(image_path, size=40, border_size=3, border_color="red"):
    img = Image.open(image_path).convert("RGBA")
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    
    bordered_size = size + border_size * 2
    border_img = Image.new("RGBA", (bordered_size, bordered_size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_img)
    border_draw.ellipse((0, 0, bordered_size, bordered_size), fill=border_color)
    border_img.paste(img, (border_size, border_size), img)
    
    return border_img

# === LOAD DATA === #
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')
df = df.sort_values('Date').reset_index(drop=True)

# === STORAGE === #
line_data = {}
bar_data = []

# === PROCESS EACH PRESIDENT === #
for president, (date_str, img_file, color) in inaugurations.items():
    start_date = pd.to_datetime(date_str)

    try:
        start_row = df[df['Date'] >= start_date].iloc[0]
        start_index = df[df['Date'] == start_row['Date']].index[0]

        future_df = df.iloc[start_index:]
        max_days = min(200, (future_df[future_df['Date'] <= TODAY]).shape[0])
        if max_days < 5:
            print(f"Not enough data for {president}")
            continue

        window = df.iloc[start_index:start_index + max_days]
        start_price = window.iloc[0][PRICE_COLUMN]
        gains = (window[PRICE_COLUMN] - start_price) / start_price * 100
        gains = gains.reset_index(drop=True)

        # Store for line graph
        line_data[president] = {
            "gains": gains,
            "color": color,
            "img": os.path.join(IMAGE_DIR, img_file)
        }

        # Store for bar graph (200th day gain or most recent)
        bar_data.append((president, gains.iloc[-1], color))

    except Exception as e:
        print(f"Error processing {president}: {e}")

# === PLOT BAR CHART === #
plt.figure("200-Day % Gain Bar Chart", figsize=(10, 6))
names = [x[0] for x in bar_data]
gains = [x[1] for x in bar_data]
colors = [x[2] for x in bar_data]
plt.bar(names, gains, color=colors)
plt.title("S&P 500 Gain After 200 Trading Days")
plt.ylabel("Gain (%)")
plt.grid(True)

# === PLOT LINE CHART === #
fig, ax = plt.subplots(figsize=(12, 7))
for name, data in line_data.items():
    gains = data["gains"]
    ax.plot(gains, label=name, color=data["color"], linewidth=2)

    # Add image at end
    image_path = data["img"]
    if os.path.exists(image_path):
        img = circular_crop_with_border(image_path, border_color=data["color"])
        im = OffsetImage(img, zoom=0.6)
        ab = AnnotationBbox(im, (len(gains) - 1, gains.iloc[-1]), frameon=False, pad=0.2)
        ax.add_artist(ab)
    else:
        print(f"Missing image for {name}: {image_path}")

ax.set_title("S&P 500 Cumulative % Gain Over First 200 Trading Days")
ax.set_xlabel("Trading Days Since Inauguration")
ax.set_ylabel("Cumulative % Gain")
ax.legend()
ax.grid(True)
plt.tight_layout()

# === SHOW BOTH GRAPHS === #
plt.show()
