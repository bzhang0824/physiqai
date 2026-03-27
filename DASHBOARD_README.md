# PhysiqAI Project Dashboard

Visual project management tool for building the PhysiqAI MVP.

---

## 🚀 How to Use

### Opening the Dashboard

**Option 1: Double-click**
```bash
# Navigate to the folder
cd ~/Documents/physiqai/

# Open in browser
open project-dashboard.html
```

**Option 2: VSCode Live Server**
```bash
# Open in VSCode
code ~/Documents/physiqai/

# Right-click project-dashboard.html → "Open with Live Server"
```

The dashboard will open at `http://localhost:5500/project-dashboard.html`

---

## 📊 Dashboard Features

### 1. **Overview Stats** (Top of page)
- **Project Progress** - Overall completion percentage
- **Current Week** - Which week you're in
- **Days Elapsed** - How many days since start
- **Budget Used** - Track spending
- **Tasks Completed** - Progress indicator
- **Beta Users** - User acquisition tracking

### 2. **Timeline View** (📅 Tab)
**What it shows:**
- All 6 weeks laid out chronologically
- Deliverables for each week
- Progress bars for completion
- Status indicators (Pending/In Progress/Completed)

**How to use:**
- Check off deliverables as you complete them
- Progress automatically updates
- Click checkbox → saves instantly

### 3. **Kanban Board** (📋 Tab)
**What it shows:**
- Tasks organized by status:
  - 📋 Backlog
  - 🏃 In Progress
  - ✅ Done
  - 🚨 Blocked

**How to use:**
- View all tasks at a glance
- See what's currently in progress
- Track blockers
- (Future: drag-and-drop to move tasks)

### 4. **Daily Log** (📝 Tab)
**What it shows:**
- Daily entries with:
  - Status (On Track/Delayed/Blocked)
  - Hours worked
  - Tasks completed
  - Blockers/notes

**How to use:**
1. Fill out form at end of each day
2. Select status (🟢🟡🔴)
3. Enter hours worked
4. List completed tasks (one per line)
5. Add any blockers or notes
6. Click "Save Entry"

**Example:**
```
Status: 🟢 On Track
Hours: 4
Tasks:
- Set up Reddit API
- Built basic scraper
- Tested on 10 posts
Blockers: None
```

### 5. **Metrics** (📊 Tab)
**What it tracks:**
- **Velocity** - Tasks completed per week
- **Avg Hours/Day** - Your daily time investment
- **Burn Rate** - Weekly spending
- **On-Time %** - Milestone completion rate

**How to use:**
- Check weekly to see trends
- Identify if pace is sustainable
- Adjust schedule if falling behind

### 6. **Notes** (💭 Tab)
**What it's for:**
- Important decisions
- Insights or learnings
- Ideas to remember
- Pivot points

**How to use:**
- Type note in text box
- Click "Add Note"
- Notes auto-timestamped
- Latest notes shown first

---

## 💾 Data Storage

**Where data is saved:**
- Browser's `localStorage`
- Persists across sessions
- Survives browser restarts

**Backup your data:**
```bash
# Data is saved in browser, so keep dashboard file safe
# Consider committing to Git weekly
git add project-dashboard.html
git commit -m "Week X progress"
git push
```

**Export data** (future feature):
- Will add CSV/JSON export
- For now, take screenshots weekly

---

## 🎯 Daily Workflow

**Every Morning (9 AM):**
1. Open dashboard
2. Check current week's deliverables
3. Review yesterday's entry
4. Plan today's tasks

**Throughout Day:**
- Update Kanban as you work
- Move tasks to "In Progress"
- Check off deliverables when done

**End of Day (5-6 PM):**
1. Go to Daily Log tab
2. Fill out today's entry
3. Review progress
4. Plan tomorrow

**Friday Afternoon:**
1. Check Metrics tab
2. Review week's progress
3. Add summary note
4. Plan next week's focus

---

## 📋 Weekly Checklist

**Week 1:**
- [ ] Set up all APIs and services
- [ ] Complete Reddit scraper
- [ ] Collect 500 transformations
- [ ] GitHub repo organized
- [ ] Body analysis working

**Week 2:**
- [ ] Build 2.5D avatar
- [ ] Morphing engine working
- [ ] Workout logger complete
- [ ] Daily updates automated

**Week 3:**
- [ ] Landing page live
- [ ] 10 beta users signed up
- [ ] Feedback collected

---

## 🚨 When to Update Dashboard

### Update Budget
When you pay for services:
1. Open browser console (F12)
2. Type: `projectData.budgetUsed = 35` (your amount)
3. Type: `saveData()`
4. Dashboard updates

### Update Beta Users
When users sign up:
1. Open console (F12)
2. Type: `projectData.betaUsers = 5` (your count)
3. Type: `saveData()`

### Change Current Week
At start of new week:
1. Open console (F12)
2. Type: `projectData.currentWeek = 2` (new week number)
3. Update week status:
   ```javascript
   projectData.weeks[0].status = 'completed'
   projectData.weeks[1].status = 'in-progress'
   saveData()
   ```

---

## 🎨 Customization

**Change colors:**
Edit `<style>` section in HTML:
- Primary color: `#667eea` → your color
- Progress bar: `.fill { background: #667eea; }`

**Add more weeks:**
Edit `projectData.weeks` array in `<script>` section

**Add more tasks:**
Edit `projectData.tasks` array

---

## 🐛 Troubleshooting

**Dashboard not loading?**
- Make sure you're opening the HTML file
- Try a different browser (Chrome recommended)
- Check browser console for errors (F12)

**Data disappeared?**
- Check if you cleared browser cache
- Browser's localStorage might be full
- Restore from Git if you committed

**Changes not saving?**
- JavaScript might be blocked
- Try different browser
- Check console for errors

---

## 💡 Pro Tips

1. **Screenshot weekly progress** - Visual record of journey
2. **Commit to Git daily** - Never lose your tracking
3. **Be honest in Daily Log** - Accurate data helps planning
4. **Review Metrics Friday** - Catch issues early
5. **Use Notes for pivots** - Document important decisions

---

## 🔮 Future Enhancements

Coming soon:
- [ ] Drag-and-drop Kanban
- [ ] Export to CSV/PDF
- [ ] Charts and graphs
- [ ] Team collaboration
- [ ] Mobile responsive
- [ ] Time tracking integration

---

**Dashboard Version:** 1.0
**Last Updated:** 2026-02-12
**Built for:** PhysiqAI MVP (6-week sprint)
