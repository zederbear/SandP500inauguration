import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Circle
from PIL import Image, ImageOps, ImageDraw
import os
import random

# === SETTINGS === #
SP500_CSV = 'sp500.csv'
DJIA_CSV = 'DJIA.csv'
IMAGE_DIR = 'images'
PRICE_COLUMN = 'Close'
TODAY = pd.to_datetime("2025-04-10")

# === PRESIDENT DATA === #
inaugurations = {
    "Ronald Reagan (2nd Term)": ("1985-01-20", "reagan.png"),
    "George H. W. Bush": ("1989-01-20", "bush_sr.png"),
    "Bill Clinton": ("1993-01-20", "clinton.png"),
    "Bill Clinton (2nd Term)": ("1997-01-20", "clinton.png"),
    "George W. Bush": ("2001-01-20", "bush.png"),
    "George W. Bush (2nd Term)": ("2005-01-20", "bush.png"),
    "Barack Obama": ("2009-01-20", "obama.png"),
    "Barack Obama (2nd Term)": ("2013-01-20", "obama.png"),
    "Donald Trump": ("2017-01-20", "trump.png"),
    "Joe Biden": ("2021-01-20", "biden.png"),
    "Donald Trump (2nd Term)": ("2025-01-20", "trump2.png")
}

# Generate random colors for each president
colors = ['#%06x' % random.randint(0, 0xFFFFFF) for _ in range(len(inaugurations))]
president_colors = {president: colors[i] for i, president in enumerate(inaugurations.keys())}

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

def plot_lines_and_images(ax, line_data, used_positions, min_distance=3):
    for name, data in line_data.items():
        gains = data["gains"]
        ax.plot(gains, label=name, color=data["color"], linewidth=2)
        image_path = data["img"]
        if os.path.exists(image_path):
            max_attempts = 50
            for _ in range(max_attempts):
                x_pos = random.randint(5, len(gains)-5)
                y_pos = gains.iloc[x_pos]
                if not any(abs(x_pos - ux) < min_distance and abs(y_pos - uy) < min_distance 
                          for ux, uy in used_positions):
                    used_positions.append((x_pos, y_pos))
                    img = circular_crop_with_border(image_path, border_color=data["color"])
                    im = OffsetImage(img, zoom=0.6)
                    ab = AnnotationBbox(im, (x_pos, y_pos), frameon=False, pad=0.2)
                    ax.add_artist(ab)
                    break
        else:
            print(f"Missing image for {name}: {image_path}")

# === LOAD DATA === #
sp500_df = pd.read_csv(SP500_CSV)
sp500_df.columns = sp500_df.columns.str.strip()
sp500_df['Date'] = pd.to_datetime(sp500_df['Date'], format='%m/%d/%y')
sp500_df = sp500_df.sort_values('Date').reset_index(drop=True)

djia_df = pd.read_csv(DJIA_CSV)
djia_df.columns = djia_df.columns.str.strip()
djia_df['Date'] = pd.to_datetime(djia_df['Date'], format='%m/%d/%y')
djia_df = djia_df.sort_values('Date').reset_index(drop=True)

# === STORAGE === #
sp500_line_data = {}
sp500_bar_data = []
djia_line_data = {}
djia_bar_data = []

# === PROCESS EACH PRESIDENT === #
for president, (date_str, img_file) in inaugurations.items():
    start_date = pd.to_datetime(date_str)

    # Process S&P 500
    try:
        start_row = sp500_df[sp500_df['Date'] >= start_date].iloc[0]
        start_index = sp500_df[sp500_df['Date'] == start_row['Date']].index[0]
        future_df = sp500_df.iloc[start_index:]
        max_days = min(200, (future_df[future_df['Date'] <= TODAY]).shape[0])
        if max_days < 5:
            print(f"Not enough SP500 data for {president}")
            continue
        window = sp500_df.iloc[start_index:start_index + max_days]
        start_price = window.iloc[0][PRICE_COLUMN]
        gains = (window[PRICE_COLUMN] - start_price) / start_price * 100
        gains = gains.reset_index(drop=True)
        sp500_line_data[president] = {
            "gains": gains,
            "color": president_colors[president],
            "img": os.path.join(IMAGE_DIR, img_file)
        }
        sp500_bar_data.append((president, gains.iloc[-1], president_colors[president]))
    except Exception as e:
        print(f"Error processing SP500 for {president}: {e}")

    # Process DJIA
    try:
        start_row = djia_df[djia_df['Date'] >= start_date].iloc[0]
        start_index = djia_df[djia_df['Date'] == start_row['Date']].index[0]
        future_df = djia_df.iloc[start_index:]
        max_days = min(200, (future_df[future_df['Date'] <= TODAY]).shape[0])
        if max_days < 5:
            print(f"Not enough DJIA data for {president}")
            continue
        window = djia_df.iloc[start_index:start_index + max_days]
        start_price = window.iloc[0][PRICE_COLUMN]
        gains = (window[PRICE_COLUMN] - start_price) / start_price * 100
        gains = gains.reset_index(drop=True)
        djia_line_data[president] = {
            "gains": gains,
            "color": president_colors[president],
            "img": os.path.join(IMAGE_DIR, img_file)
        }
        djia_bar_data.append((president, gains.iloc[-1], president_colors[president]))
    except Exception as e:
        print(f"Error processing DJIA for {president}: {e}")

# === PLOT ALL CHARTS === #
plt.figure("SP500 200-Day % Gain Bar Chart", figsize=(10, 6))
names = [x[0] for x in sp500_bar_data]
gains = [x[1] for x in sp500_bar_data]
colors = [x[2] for x in sp500_bar_data]
plt.bar(names, gains, color=colors)
plt.title("S&P 500 Gain After 200 Trading Days")
plt.ylabel("Gain (%)")
plt.grid(True)

plt.figure("DJIA 200-Day % Gain Bar Chart", figsize=(10, 6))
names = [x[0] for x in djia_bar_data]
gains = [x[1] for x in djia_bar_data]
colors = [x[2] for x in djia_bar_data]
plt.bar(names, gains, color=colors)
plt.title("Dow Jones Gain After 200 Trading Days")
plt.ylabel("Gain (%)")
plt.grid(True)

# Plot SP500 Line Chart
fig_sp500, ax_sp500 = plt.subplots(figsize=(12, 7))
used_positions = []
plot_lines_and_images(ax_sp500, sp500_line_data, used_positions)
ax_sp500.set_title("S&P 500 Cumulative % Gain Over First 200 Trading Days")
ax_sp500.set_xlabel("Trading Days Since Inauguration")
ax_sp500.set_ylabel("Cumulative % Gain")
ax_sp500.legend()
ax_sp500.grid(True)

# Plot DJIA Line Chart
fig_djia, ax_djia = plt.subplots(figsize=(12, 7))
used_positions = []
plot_lines_and_images(ax_djia, djia_line_data, used_positions)
ax_djia.set_title("Dow Jones Cumulative % Gain Over First 200 Trading Days")
ax_djia.set_xlabel("Trading Days Since Inauguration")
ax_djia.set_ylabel("Cumulative % Gain")
ax_djia.legend()
ax_djia.grid(True)

plt.tight_layout()
plt.show()
