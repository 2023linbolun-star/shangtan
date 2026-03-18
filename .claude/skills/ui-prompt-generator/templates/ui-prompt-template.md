---
name: ui-prompt-template
description: UI 原型图提示词输出模板。当需要生成文生图提示词时，按照此模板的结构和格式填充内容，输出为 UI-Prompts.md 文件。
---

# UI 原型图提示词模板

本模板用于生成可直接用于 AI 绘图工具的原型图提示词。生成时按照此结构填充内容。

---

## 文件命名

`UI-Prompts.md`

---

## 提示词结构

每条提示词按以下结构组织：

```
[主体] + [布局] + [控件] + [风格] + [质量词]
```

### [主体]
产品类型 + 界面类型 + 页面名称

示例：
- `A modern web application UI for a storyboard generator tool, main interface`
- `A mobile app screen for a task management application, settings page`

### [布局]
整体结构 + 比例 + 区域划分

示例：
- `split layout with left panel (40%) and right content area (60%)`
- `single column layout with top navigation bar and main content below`
- `grid layout with 2x2 card arrangement`

### [控件]
各区域的具体控件，从上到下、从左到右描述

示例：
- `left panel contains: project name input at top, large text area for content, dropdown menu for style selection, primary action button at bottom`
- `right panel shows: 3x3 grid of image cards with frame numbers and captions, action buttons below`

### [风格]
视觉风格 + 配色 + 细节特征

| 风格 | 英文描述 |
|------|---------|
| 现代极简 | minimalist design, clean layout, ample white space, subtle shadows |
| 玻璃拟态 | glassmorphism style, frosted glass effect, translucent panels, blur background |
| 新拟态 | neumorphism design, soft shadows, subtle highlights, extruded elements |
| 便当盒布局 | bento grid layout, modular cards, organized sections, clean borders |
| 暗黑模式 | dark mode UI, dark background, light text, subtle glow effects |
| 新野兽派 | neo-brutalist design, bold black borders, high contrast, raw aesthetic |

配色描述：
- 浅色系：`light color scheme, white background, dark text, [accent color] accent`
- 深色系：`dark color scheme, dark gray background, light text, [accent color] accent`

### [质量词]
确保生成质量的关键词，放在提示词末尾

```
UI/UX design, high fidelity mockup, 4K resolution, professional, Figma style, dribbble, behance
```

---

## 输出格式

```markdown
# [产品名称] 原型图提示词

> 视觉风格：[风格名称]
> 配色方案：[配色名称]
> 目标平台：[平台名称]

---

## 页面 1：[页面名称]

**页面说明**：[一句话描述这个页面是什么]

**提示词**：
```
[完整的英文提示词]
```

---

## 页面 2：[页面名称]

**页面说明**：[一句话描述]

**提示词**：
```
[完整的英文提示词]
```
```

---

## 完整示例

以下是「剧本分镜生成器」的原型图提示词示例，供参考：

```markdown
# 剧本分镜生成器 原型图提示词

> 视觉风格：现代极简（Minimalism）
> 配色方案：浅色系
> 目标平台：网页（Web）

---

## 页面 1：主界面

**页面说明**：用户输入剧本、设置角色和场景、生成分镜图的主要工作界面

**提示词**：
```
A modern web application UI for a storyboard generator tool, main interface, split layout with left input panel (40% width) and right output area (60% width), left panel contains: project name input field at top, large multiline text area for script input with placeholder text, character cards section with image thumbnails and text fields and add button, scene cards section below, style dropdown menu, prominent generate button at bottom, right panel shows: 3x3 grid of storyboard image cards with frame numbers and short descriptions below each image, download all button and continue generating button below the grid, page navigation at bottom, minimalist design, clean layout, white background, light gray borders, blue accent color for primary actions, subtle shadows, rounded corners, UI/UX design, high fidelity mockup, 4K resolution, professional, Figma style
```

---

## 页面 2：空状态界面

**页面说明**：用户首次打开、尚未输入内容时的引导界面

**提示词**：
```
A modern web application UI for a storyboard generator tool, empty state screen, split layout with left panel (40%) and right panel (60%), left panel shows: empty input fields with placeholder text and helper icons, right panel displays: large empty state illustration in the center, welcome message and getting started tips below, minimalist design, clean layout, white background, soft gray placeholder elements, blue accent color, friendly and inviting atmosphere, UI/UX design, high fidelity mockup, 4K resolution, professional, Figma style
```
```

---

## 写作要点

1. **提示词语言**：始终使用英文，AI 绘图工具对英文理解更好
2. **结构完整**：确保包含主体、布局、控件、风格、质量词五个部分
3. **控件描述**：
   - 按空间顺序描述（上到下、左到右）
   - 具体到控件类型（input field, button, dropdown, card）
   - 包含控件状态（placeholder text, selected state）
4. **布局比例**：写明具体比例（40%/60%），不要只说「左右布局」
5. **风格一致**：同一产品的多个页面使用相同的风格描述
6. **质量词**：始终在末尾加上质量词确保生成效果
7. **页面说明**：用中文写一句话说明，帮助理解这个页面是什么
