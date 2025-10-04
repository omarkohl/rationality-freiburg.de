# Meetup Generation Template

Copy and paste this entire template into an LLM chat, then fill in the details at the bottom:

---

Create a new rationality meetup for the website. Follow these instructions:

1. Create a new directory with the format `YYYY-MM-DD-[slug-from-title]` in
   `./website/content/events/`

2. Generate an English `_index.md` file with:
   - Proper Hugo frontmatter including title, date, eventStart, eventEnd, eventLocation, eventHost, eventType
   - Standard location: "Veranstaltungsraum, Haus des Engagements, Rehlingstraße 9, 79100 Freiburg"
   - Standard coordinates: eventGeoLat: 47.98953, eventGeoLon: 7.83979
   - Standard meetup and LW links
   - Event time: 18:00-20:30 local time (CEST/CET depending on date)
   - Include the provided preparation and description content
   - Add standard organization section with host information
   - Include location map and "Other" section with cover image reference

3. Generate a German `_index.de.md` file with:
   - Natural German translation of all content
   - German URL slug based on the German title (format:
     `termine/YYYY-MM-DD-[german-slug]`)
   - All the same structure as English version

4. Create descriptive alt text for both languages that captures the meetup
   theme and would work well for image generation

5. Output an image generation prompt in the chat that is:
   - Friendly and inviting for a meetup atmosphere
   - Based on the alt text but enhanced for visual appeal
   - Warm and welcoming rather than intimidating
   - Suitable for the specific topic
   - Format: 512x512 square

6. Convert the provided date from DD.MM format to proper datetime, determine
   the correct day of the week

Fill in these details:

Date: [DD.MM format]
Host: [Host name]
Title: [Meetup title]
Preparation: [Requirements or "None."]
What we will do: [Detailed description]