"""
Content Templates Library for XThreadMaster
Pre-written, proven templates for viral content across X, LinkedIn, and Instagram
"""

TEMPLATES = [
    # ============================================
    # FREE TEMPLATES (5 total - 1 per category)
    # ============================================

    # SaaS - FREE
    {
        "id": "saas_launch",
        "title": "Product Launch Announcement",
        "category": "SaaS",
        "platform": "X Thread",
        "tier": "free",
        "template": """🚀 We just launched {product_name}!

After {time_period} of building, we're finally live.

Here's what makes it different:

{feature_1}
{feature_2}
{feature_3}

Built for {target_audience} who are tired of {pain_point}.

Try it free: {url}

What feature should we build next? 👇""",
        "placeholders": {
            "product_name": "your product name",
            "time_period": "6 months/1 year/etc",
            "feature_1": "first unique feature",
            "feature_2": "second unique feature",
            "feature_3": "third unique feature",
            "target_audience": "developers/founders/marketers/etc",
            "pain_point": "the problem you solve",
            "url": "your website"
        },
        "example": "Product launch thread for a new SaaS tool"
    },

    # Personal Brand - FREE
    {
        "id": "personal_lesson",
        "title": "Life Lesson Thread",
        "category": "Personal Brand",
        "platform": "X Thread",
        "tier": "free",
        "template": """I {action} and learned {number} lessons the hard way.

Here's what nobody tells you:

1/ {lesson_1}

2/ {lesson_2}

3/ {lesson_3}

The biggest surprise? {surprise}

If you're {target_audience}, save this thread. You'll need it.""",
        "placeholders": {
            "action": "quit my job/started a company/learned to code/etc",
            "number": "3/5/7",
            "lesson_1": "first lesson",
            "lesson_2": "second lesson",
            "lesson_3": "third lesson",
            "surprise": "unexpected insight",
            "target_audience": "starting your journey/building something/etc"
        },
        "example": "Personal experience sharing thread"
    },

    # Marketing - FREE
    {
        "id": "marketing_growth",
        "title": "Growth Hack Case Study",
        "category": "Marketing",
        "platform": "LinkedIn Post",
        "tier": "free",
        "template": """🎯 We grew from {start_number} to {end_number} {metric} in {time_period}.

Here's the exact strategy we used:

**The Problem:**
{problem_description}

**The Solution:**
We implemented {strategy_name}. Here's how it works:

✅ {step_1}
✅ {step_2}
✅ {step_3}

**The Results:**
• {result_1}
• {result_2}
• {result_3}

The key insight? {key_insight}

Want to try this for your business? Drop a comment and I'll send you our full playbook. 📊

#{hashtag_1} #{hashtag_2} #{hashtag_3}""",
        "placeholders": {
            "start_number": "0/100/1K/etc",
            "end_number": "10K/100K/1M/etc",
            "metric": "users/followers/customers/revenue/etc",
            "time_period": "30 days/3 months/1 year/etc",
            "problem_description": "what you were struggling with",
            "strategy_name": "the strategy you used",
            "step_1": "first step",
            "step_2": "second step",
            "step_3": "third step",
            "result_1": "first result",
            "result_2": "second result",
            "result_3": "third result",
            "key_insight": "main takeaway",
            "hashtag_1": "relevant hashtag",
            "hashtag_2": "relevant hashtag",
            "hashtag_3": "relevant hashtag"
        },
        "example": "Growth marketing case study for LinkedIn"
    },

    # Crypto - FREE
    {
        "id": "crypto_project",
        "title": "Crypto Project Update",
        "category": "Crypto",
        "platform": "X Thread",
        "tier": "free",
        "template": """GM! 🌅 {project_name} update thread 🧵

This {time_period} has been insane. Here's what we shipped:

🔥 {update_1}
🔥 {update_2}
🔥 {update_3}

Community grew to {community_size} holders 💎

Next up: {upcoming_feature}

Still early. Mint: {url}

LFG! 🚀""",
        "placeholders": {
            "project_name": "your project name",
            "time_period": "week/month/quarter",
            "update_1": "first update",
            "update_2": "second update",
            "update_3": "third update",
            "community_size": "1K/10K/100K",
            "upcoming_feature": "what's next",
            "url": "mint/website link"
        },
        "example": "Crypto project update thread"
    },

    # Fitness - FREE
    {
        "id": "fitness_transformation",
        "title": "Transformation Story",
        "category": "Fitness",
        "platform": "Instagram Carousel",
        "tier": "free",
        "template": """SLIDE 1: {time_period} Transformation 💪

SLIDE 2: Where I Started
{starting_point}

SLIDE 3: What Changed
{change_1}

SLIDE 4: The Workout
{workout_description}

SLIDE 5: The Diet
{diet_description}

SLIDE 6: Biggest Lesson
{lesson}

SLIDE 7: Your Turn
{call_to_action}""",
        "placeholders": {
            "time_period": "90 Day/6 Month/1 Year/etc",
            "starting_point": "where you began",
            "change_1": "first major change",
            "workout_description": "workout routine",
            "diet_description": "diet approach",
            "lesson": "key learning",
            "call_to_action": "next steps for audience"
        },
        "example": "Fitness transformation carousel"
    },

    # ============================================
    # PRO TEMPLATES (45+ more)
    # ============================================

    # SaaS - PRO
    {
        "id": "saas_milestone",
        "title": "Revenue Milestone",
        "category": "SaaS",
        "platform": "X Thread",
        "tier": "pro",
        "template": """We just hit {revenue} MRR 🎉

Started {time_ago} with {starting_revenue}.

Here's everything that worked (and what didn't):

✅ What worked:
• {success_1}
• {success_2}
• {success_3}

❌ What failed:
• {failure_1}
• {failure_2}

Biggest lesson: {lesson}

Next stop: {next_goal}

Questions? Ask below 👇""",
        "placeholders": {
            "revenue": "$10K/$100K/$1M/etc",
            "time_ago": "6 months ago/last year/etc",
            "starting_revenue": "$0/$1K/etc",
            "success_1": "strategy that worked",
            "success_2": "strategy that worked",
            "success_3": "strategy that worked",
            "failure_1": "what didn't work",
            "failure_2": "what didn't work",
            "lesson": "key takeaway",
            "next_goal": "next milestone"
        },
        "example": "Revenue milestone announcement"
    },

    {
        "id": "saas_customer_story",
        "title": "Customer Success Story",
        "category": "SaaS",
        "platform": "LinkedIn Post",
        "tier": "pro",
        "template": """💼 Customer Spotlight: How {customer_name} achieved {result}

{customer_name} came to us with a challenge:
{problem}

Here's what happened next:

**Week 1:** {week1_activity}
**Week 2:** {week2_activity}
**Week 4:** {week4_result}

The results speak for themselves:
📈 {metric_1}
📈 {metric_2}
📈 {metric_3}

"{testimonial_quote}" - {customer_name}, {customer_title}

Ready to achieve similar results? Let's talk. 👇

#{hashtag_1} #{hashtag_2} #{hashtag_3}""",
        "placeholders": {
            "customer_name": "customer or company name",
            "result": "the outcome achieved",
            "problem": "their initial challenge",
            "week1_activity": "what happened in week 1",
            "week2_activity": "what happened in week 2",
            "week4_result": "result after 4 weeks",
            "metric_1": "measurable result",
            "metric_2": "measurable result",
            "metric_3": "measurable result",
            "testimonial_quote": "customer quote",
            "customer_title": "their role/title",
            "hashtag_1": "relevant hashtag",
            "hashtag_2": "relevant hashtag",
            "hashtag_3": "relevant hashtag"
        },
        "example": "Customer success story for LinkedIn"
    },

    # Personal Brand - PRO
    {
        "id": "personal_contrarian",
        "title": "Contrarian Take",
        "category": "Personal Brand",
        "platform": "X Thread",
        "tier": "pro",
        "template": """Unpopular opinion: {controversial_statement}

Everyone says {common_belief}.

But after {experience}, I realized the opposite is true.

Here's why:

1/ {reason_1}

2/ {reason_2}

3/ {reason_3}

The data backs this up: {data_point}

Most people won't believe this until {trigger_event}.

But you? You can get ahead now.

Here's how: {action_step}""",
        "placeholders": {
            "controversial_statement": "your contrarian view",
            "common_belief": "what everyone thinks",
            "experience": "your experience/research",
            "reason_1": "first supporting reason",
            "reason_2": "second supporting reason",
            "reason_3": "third supporting reason",
            "data_point": "supporting data",
            "trigger_event": "what changes minds",
            "action_step": "what to do"
        },
        "example": "Contrarian opinion thread"
    },

    {
        "id": "personal_mistake",
        "title": "Costly Mistake Thread",
        "category": "Personal Brand",
        "platform": "X Thread",
        "tier": "pro",
        "template": """I made a {amount} mistake.

So you don't have to.

The situation: {context}

What I did: {wrong_action}

What happened: {consequence}

What I should have done: {right_action}

The lesson: {lesson}

If you're {target_situation}, avoid this at all costs.

You're welcome. 🙏""",
        "placeholders": {
            "amount": "$10K/$100K/career-defining/etc",
            "context": "the situation",
            "wrong_action": "what you did wrong",
            "consequence": "what happened",
            "right_action": "correct approach",
            "lesson": "key takeaway",
            "target_situation": "who this applies to"
        },
        "example": "Mistake sharing thread"
    },

    # Marketing - PRO
    {
        "id": "marketing_viral",
        "title": "Viral Content Framework",
        "category": "Marketing",
        "platform": "X Thread",
        "tier": "pro",
        "template": """This {content_type} got {engagement_number} {engagement_type}.

Here's the framework I used:

Hook: {hook_description}
↓
Problem: {problem_description}
↓
Solution: {solution_description}
↓
CTA: {cta_description}

The secret? {secret}

Use this for your next post.

You'll 10x your engagement.""",
        "placeholders": {
            "content_type": "tweet/post/video/etc",
            "engagement_number": "1M/500K/100K/etc",
            "engagement_type": "views/likes/shares/etc",
            "hook_description": "attention grabber",
            "problem_description": "pain point",
            "solution_description": "your solution",
            "cta_description": "call to action",
            "secret": "key insight"
        },
        "example": "Viral content breakdown thread"
    },

    {
        "id": "marketing_funnel",
        "title": "Marketing Funnel Breakdown",
        "category": "Marketing",
        "platform": "LinkedIn Post",
        "tier": "pro",
        "template": """🎯 Our {conversion_type} funnel converts at {percentage}%.

Here's the exact breakdown:

**Top of Funnel:**
{tof_strategy}
Result: {tof_metric}

**Middle of Funnel:**
{mof_strategy}
Result: {mof_metric}

**Bottom of Funnel:**
{bof_strategy}
Result: {bof_metric}

**The Conversion Formula:**
{formula_description}

**Tools We Use:**
1. {tool_1} - {tool_1_purpose}
2. {tool_2} - {tool_2_purpose}
3. {tool_3} - {tool_3_purpose}

The biggest lever? {biggest_lever}

Want the complete playbook? Comment "FUNNEL" below. 📈

#{hashtag_1} #{hashtag_2} #{hashtag_3}""",
        "placeholders": {
            "conversion_type": "sales/signup/demo/etc",
            "percentage": "conversion rate",
            "tof_strategy": "top of funnel approach",
            "tof_metric": "top of funnel result",
            "mof_strategy": "middle of funnel approach",
            "mof_metric": "middle of funnel result",
            "bof_strategy": "bottom of funnel approach",
            "bof_metric": "bottom of funnel result",
            "formula_description": "conversion formula",
            "tool_1": "first tool",
            "tool_1_purpose": "why you use it",
            "tool_2": "second tool",
            "tool_2_purpose": "why you use it",
            "tool_3": "third tool",
            "tool_3_purpose": "why you use it",
            "biggest_lever": "key insight",
            "hashtag_1": "relevant hashtag",
            "hashtag_2": "relevant hashtag",
            "hashtag_3": "relevant hashtag"
        },
        "example": "Marketing funnel case study"
    },

    # Crypto - PRO
    {
        "id": "crypto_alpha",
        "title": "Alpha Thread",
        "category": "Crypto",
        "platform": "X Thread",
        "tier": "pro",
        "template": """🚨 ALPHA: {project_category} play everyone's sleeping on

Been researching {project_name} for {time_period}.

Here's why it's early:

📊 Metrics:
• FDV: {fdv}
• Holders: {holders}
• Volume: {volume}

🔍 Why it's special:
{unique_angle_1}
{unique_angle_2}
{unique_angle_3}

📈 Catalysts:
{catalyst_1}
{catalyst_2}

Not financial advice. DYOR. {url}

GM to whoever sees this early. 🌅""",
        "placeholders": {
            "project_category": "DeFi/NFT/GameFi/etc",
            "project_name": "project name",
            "time_period": "3 weeks/2 months/etc",
            "fdv": "fully diluted valuation",
            "holders": "number of holders",
            "volume": "trading volume",
            "unique_angle_1": "differentiator",
            "unique_angle_2": "differentiator",
            "unique_angle_3": "differentiator",
            "catalyst_1": "upcoming event",
            "catalyst_2": "upcoming event",
            "url": "project link"
        },
        "example": "Crypto alpha thread"
    },

    {
        "id": "crypto_market",
        "title": "Market Analysis",
        "category": "Crypto",
        "platform": "X Thread",
        "tier": "pro",
        "template": """{market_indicator} just {action}.

What this means for crypto:

📉 Short term ({timeframe_1}):
{short_term_prediction}

📈 Medium term ({timeframe_2}):
{medium_term_prediction}

🎯 What I'm watching:
• {watchpoint_1}
• {watchpoint_2}
• {watchpoint_3}

💼 Portfolio moves:
{portfolio_action}

History says: {historical_pattern}

Stay safe out there. 🛡️""",
        "placeholders": {
            "market_indicator": "BTC/ETH/SPX/etc",
            "action": "broke resistance/hit support/etc",
            "timeframe_1": "24-48hrs/this week/etc",
            "short_term_prediction": "short term outlook",
            "timeframe_2": "next month/Q4/etc",
            "medium_term_prediction": "medium term outlook",
            "watchpoint_1": "key indicator",
            "watchpoint_2": "key indicator",
            "watchpoint_3": "key indicator",
            "portfolio_action": "your moves",
            "historical_pattern": "historical context"
        },
        "example": "Market analysis thread"
    },

    # Fitness - PRO
    {
        "id": "fitness_routine",
        "title": "Workout Routine Breakdown",
        "category": "Fitness",
        "platform": "Instagram Carousel",
        "tier": "pro",
        "template": """SLIDE 1: {workout_name} 🔥

SLIDE 2: Who This Is For
{target_audience}

SLIDE 3: Day 1 - {day1_focus}
{day1_exercises}

SLIDE 4: Day 2 - {day2_focus}
{day2_exercises}

SLIDE 5: Day 3 - {day3_focus}
{day3_exercises}

SLIDE 6: Nutrition Protocol
{nutrition_tips}

SLIDE 7: Common Mistakes
{mistakes_to_avoid}

SLIDE 8: Expected Results
{expected_results}

SLIDE 9: Get Started
{call_to_action}""",
        "placeholders": {
            "workout_name": "program name",
            "target_audience": "who should do this",
            "day1_focus": "focus area",
            "day1_exercises": "exercises for day 1",
            "day2_focus": "focus area",
            "day2_exercises": "exercises for day 2",
            "day3_focus": "focus area",
            "day3_exercises": "exercises for day 3",
            "nutrition_tips": "nutrition advice",
            "mistakes_to_avoid": "common errors",
            "expected_results": "what to expect",
            "call_to_action": "next steps"
        },
        "example": "Workout routine carousel"
    },

    {
        "id": "fitness_myth",
        "title": "Fitness Myth Buster",
        "category": "Fitness",
        "platform": "X Thread",
        "tier": "pro",
        "template": """MYTH: {myth_statement}

REALITY: {reality_statement}

Let me explain...

The science: {scientific_explanation}

Why everyone gets this wrong: {why_misunderstood}

What you should do instead:
✅ {correct_approach_1}
✅ {correct_approach_2}
✅ {correct_approach_3}

Results you'll see: {expected_results}

Share this. 99% of people believe the myth.""",
        "placeholders": {
            "myth_statement": "common myth",
            "reality_statement": "the truth",
            "scientific_explanation": "science behind it",
            "why_misunderstood": "why myth persists",
            "correct_approach_1": "right way",
            "correct_approach_2": "right way",
            "correct_approach_3": "right way",
            "expected_results": "outcomes"
        },
        "example": "Fitness myth busting thread"
    },

    # General/Viral - PRO
    {
        "id": "general_list",
        "title": "Ultimate List Thread",
        "category": "General",
        "platform": "X Thread",
        "tier": "pro",
        "template": """{number} {topic} that {benefit}.

A thread 🧵

1/ {item_1}
{description_1}

2/ {item_2}
{description_2}

3/ {item_3}
{description_3}

4/ {item_4}
{description_4}

5/ {item_5}
{description_5}

Bookmark this. You'll thank me later.

Which one are you trying first?""",
        "placeholders": {
            "number": "5/7/10/etc",
            "topic": "tools/tips/hacks/books/etc",
            "benefit": "changed my life/made me money/etc",
            "item_1": "first item",
            "description_1": "why it's valuable",
            "item_2": "second item",
            "description_2": "why it's valuable",
            "item_3": "third item",
            "description_3": "why it's valuable",
            "item_4": "fourth item",
            "description_4": "why it's valuable",
            "item_5": "fifth item",
            "description_5": "why it's valuable"
        },
        "example": "List-based thread"
    },

    {
        "id": "general_story",
        "title": "Story Arc Thread",
        "category": "General",
        "platform": "X Thread",
        "tier": "pro",
        "template": """{time_ago}, {starting_situation}.

Today, {current_situation}.

Here's what happened:

ACT 1 - The Problem
{problem_description}

ACT 2 - The Struggle
{struggle_description}

ACT 3 - The Breakthrough
{breakthrough_description}

The twist: {plot_twist}

The lesson: {lesson}

If you're going through {similar_situation}, keep going.

It gets better.""",
        "placeholders": {
            "time_ago": "1 year ago/3 years ago/etc",
            "starting_situation": "where you were",
            "current_situation": "where you are now",
            "problem_description": "the initial challenge",
            "struggle_description": "the difficult period",
            "breakthrough_description": "turning point",
            "plot_twist": "unexpected element",
            "lesson": "key takeaway",
            "similar_situation": "who relates"
        },
        "example": "Narrative story thread"
    },

    {
        "id": "general_comparison",
        "title": "Before vs After",
        "category": "General",
        "platform": "LinkedIn Post",
        "tier": "pro",
        "template": """⚡ Before vs After: {transformation_topic}

**BEFORE:**
{before_state_1}
{before_state_2}
{before_state_3}

**AFTER:**
{after_state_1}
{after_state_2}
{after_state_3}

**What Changed:**
The shift happened when I {key_action}.

Here's the framework I used:

🔹 {framework_step_1}
🔹 {framework_step_2}
🔹 {framework_step_3}

**The Impact:**
• {impact_1}
• {impact_2}
• {impact_3}

The best part? {bonus_benefit}

Want to make this shift? Here's where to start: {starting_point}

#{hashtag_1} #{hashtag_2} #{hashtag_3}""",
        "placeholders": {
            "transformation_topic": "what transformed",
            "before_state_1": "before condition",
            "before_state_2": "before condition",
            "before_state_3": "before condition",
            "after_state_1": "after condition",
            "after_state_2": "after condition",
            "after_state_3": "after condition",
            "key_action": "what caused change",
            "framework_step_1": "how to do it",
            "framework_step_2": "how to do it",
            "framework_step_3": "how to do it",
            "impact_1": "result",
            "impact_2": "result",
            "impact_3": "result",
            "bonus_benefit": "extra benefit",
            "starting_point": "first step",
            "hashtag_1": "relevant hashtag",
            "hashtag_2": "relevant hashtag",
            "hashtag_3": "relevant hashtag"
        },
        "example": "Before/after transformation post"
    },
]

# Helper functions
def get_all_templates():
    """Return all templates"""
    return TEMPLATES

def get_free_templates():
    """Return only free templates"""
    return [t for t in TEMPLATES if t["tier"] == "free"]

def get_pro_templates():
    """Return only pro templates"""
    return [t for t in TEMPLATES if t["tier"] == "pro"]

def get_templates_by_category(category):
    """Get templates filtered by category"""
    return [t for t in TEMPLATES if t["category"] == category]

def get_templates_by_platform(platform):
    """Get templates filtered by platform"""
    return [t for t in TEMPLATES if t["platform"] == platform]

def get_template_by_id(template_id):
    """Get a specific template by ID"""
    for t in TEMPLATES:
        if t["id"] == template_id:
            return t
    return None

def get_categories():
    """Get all unique categories"""
    return list(set(t["category"] for t in TEMPLATES))

def fill_template(template_text, placeholders_dict):
    """Fill in template with user-provided values"""
    filled = template_text
    for key, value in placeholders_dict.items():
        filled = filled.replace(f"{{{key}}}", value)
    return filled
