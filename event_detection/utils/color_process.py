def lerp(a, b, t):
    return a * (1 - t) + b * t

def rgb2hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def getNewRandomColor(i):
    colors = ['#FF7F50', '#9D50BB', '#FFD801', '#5CB3FF', '#FF4E50', '#3EA055', '#01C6FF',
              '#FF0084', '#ADD100', '#81D8D0', '#3B9C9C', '#D38312', '#95B995', '#94FFFF', '#9481FF',
              '#2e48f2', '#4f55c6', '#5ebc2b', '#064d99', '#1e0c75', '#64158e', '#d2f740', '#f733e7',
              '#9e033b', '#fcbe67', '#3d38d8', '#4a73ad', '#59eab5', '#84e209', '#e3e562', '#9df74f',
              '#9f0ddd', '#5b95d8', '#5fcc49', '#d89038', '#f96bd3', '#4ded21', '#40a8f7', '#29999b',
              '#ad60ff', '#58c8e8', '#ff68a2', '#02156d', '#58d3b4', '#1a5f84', '#dd8339', '#1bc168',
              '#ce9d21', '#deef6b', '#a650ce', '#00c4c1', '#5ddd5f', '#2ded49', '#4dead5', '#185bf7']
    return colors[i]


def getBGRandomColor(i):
    bg_color = ['#ffc5b0', '#d2b0e0', '#ffed8c', '#b5dcff', '#ffafb0', '#a8d4b2', '#8ce5ff', '#ff8cc7', '#daea8c',
                '#c6ede9', '#a6d2d2', '#ebc794', '#cfdfcf', '#ceffff', '#cec6ff', '#a0acf9', '#afb2e5', '#b6e09f',
                '#8eaed1', '#9991c0', '#b995cc', '#eafba9', '#fba3f4', '#d38da6', '#fde1ba', '#a7a5ed', '#adc0da',
                '#b4f5dd', '#c7f190', '#f2f3b8', '#d2fbaf', '#d392ef', '#b5cfed', '#b7e8ad', '#edcda5', '#fcbceb',
                '#aef69b', '#a9d7fb', '#9ed1d2', '#dab7ff', '#b3e6f4', '#ffbbd5', '#8d95bd', '#b3ebdd', '#97b7c7',
                '#efc7a5', '#98e3bb', '#e8d29b', '#f0f7bc', '#d6b0e8', '#8ce4e3', '#b6efb7', '#a0f6ad', '#aef5ec',
                '#97b5fb']
    return bg_color[i]