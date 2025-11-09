#!/usr/bin/env python3
"""
Script to create a new event for rationality-freiburg.de website.

This script:
1. Queries the user for event details
2. Creates the event directory and files
3. Copies and resizes the cover image (if provided)
4. Commits the changes using jj
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Event template
EVENT_TEMPLATE = """---
title: "{title}"
date: {date}
eventStart: {event_start}
eventEnd: {event_end}
eventLocation: "Veranstaltungsraum, Haus des Engagements, Rehlingstraße 9, 79100 Freiburg"
eventGeoLat: 47.98953
eventGeoLon: 7.83979
meetupLink: https://www.meetup.com/de-DE/rationality-freiburg/
lwLink: https://www.lesswrong.com/groups/fFZZ2Ywzsab86EESY
description: "Where: Haus des Engagements, Rehlingstraße 9, 79100 Freiburg. When: {event_date_formatted} at {event_time} hours CEST."
eventHost:
{event_hosts}
eventType:
{event_types}
layout: single
outputs:
  - HTML
  - Calendar
---

{closed_notice}

## Preparation

To be defined.


## What will we do?

To be defined.


## Organization

You are worried you have nothing to contribute? No worries! Everyone is
welcome!

There always is a mix of German and English speakers and we configure the
discussion rounds so that everyone feels comfortable participating. The primary
language is English.

This meetup will be hosted by {event_hosts_text}.

There will be snacks and drinks.

We will go and get dinner after the meetup. Anyone who has time is welcome to
join.

![Location (Veranstaltungsraum, Haus des Engagements)](/images/hde-new-building-2.png)

<small>In the above map the location where you should leave your bikes is marked
in blue and the entrance (at the end of the metal ramp) with a red cross.</small>


## Other

[Learn more about us]({{{{< ref "about" >}}}}).

![{title}](cover.png "{title}")

<small>Image generated with _GPT 4o_.</small>
"""

CLOSED_NOTICE = """**IMPORTANT:** This is a closed meetup, meaning it is only meant for people who
have attended at least ONE previous event. Please do not come if this does not
apply to you! [Why? Read this.]({{{{< ref "posts/closed-meetups" >}}}}) Check the
[list of events]({{{{< ref "events" >}}}}) to find the next public event, where
everyone is welcome. Anything listed there is 100% open to anyone.

"""


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    return result


def get_input(prompt, default=None, required=True):
    """Get input from user with optional default value."""
    if default:
        prompt = f"{prompt} [{default}]"
    prompt += ": "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please provide a value.")


def get_date_input(prompt, default=None):
    """Get and validate date input in YYYY-MM-DD format."""
    while True:
        date_str = get_input(prompt, default)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")


def get_time_input(prompt, default="18:00"):
    """Get and validate time input in HH:MM format."""
    while True:
        time_str = get_input(prompt, default)
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Please use HH:MM format (e.g., 18:00).")


def title_to_slug(title):
    """Convert event title to URL-friendly slug."""
    # Convert to lowercase
    slug = title.lower()
    
    # Remove common articles and words
    words_to_remove = ['the', 'a', 'an']
    words = slug.split()
    words = [w for w in words if w not in words_to_remove]
    slug = ' '.join(words)
    
    # Remove punctuation and special characters, keep only alphanumeric and spaces
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def format_hosts_for_yaml(hosts):
    """Format hosts list for YAML eventHost field."""
    return "\n".join([f"  - {host}" for host in hosts])


def format_hosts_for_text(hosts):
    """Format hosts list for natural language text (e.g., 'Alice, Bob and Charlie')."""
    if len(hosts) == 1:
        return hosts[0]
    elif len(hosts) == 2:
        return f"{hosts[0]} and {hosts[1]}"
    else:
        return f"{', '.join(hosts[:-1])} and {hosts[-1]}"


def format_event_date(date_str):
    """Format date as 'Friday, December 19th' style."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Get day with suffix (1st, 2nd, 3rd, 4th, etc.)
    day = date_obj.day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    # Format as "Weekday, Month Dayth"
    return date_obj.strftime(f"%A, %B {day}{suffix}")



def main():
    # Get the repository root
    repo_root = Path(__file__).parent.parent
    website_dir = repo_root / "website"
    
    if not website_dir.exists():
        print(f"Error: website directory not found at {website_dir}")
        sys.exit(1)
    
    print("=== Create New Event for rationality-freiburg.de ===\n")
    
    # Get event details
    event_date = get_date_input("Event date (YYYY-MM-DD)", 
                                datetime.now().strftime("%Y-%m-%d"))
    
    event_title = get_input("Event title (English)")
    
    # Generate slug from title
    event_slug = title_to_slug(event_title)
    print(f"Generated slug: {event_slug}")
    confirm = get_input("Use this slug? (y/n or enter custom slug)", "y")
    if confirm.lower() != 'y' and confirm.lower() != 'yes':
        event_slug = confirm if confirm else get_input("Enter custom slug")
    
    # Create event name from date and slug
    event_name = f"{event_date}-{event_slug}"
    
    print(f"\nEvent name will be: {event_name}")
    
    event_start_time = get_time_input("Event start time (HH:MM)", "18:00")
    event_end_time = get_time_input("Event end time (HH:MM)", "20:30")
    
    print("\nEvent host names (comma-separated if multiple):")
    event_host_input = get_input("Event host(s)")
    event_hosts = [h.strip() for h in event_host_input.split(',')]
    
    print("\nEvent types (comma-separated):")
    print("  Options: discussion, exercise, social, presentation")
    event_types_input = get_input("Event types", "discussion")
    event_types = [t.strip() for t in event_types_input.split(',')]
    
    is_closed = get_input("Is this a closed meetup? (y/n)", "n").lower() == 'y'
    
    cover_image_path = get_input("Path to cover image (leave empty to skip)", 
                                 default="", required=False)
    
    # Prepare event directory
    event_dir = website_dir / "content" / "events" / event_name
    
    if event_dir.exists():
        print(f"\nError: Event directory already exists: {event_dir}")
        sys.exit(1)
    
    # Create event directory
    print("\nCreating event structure...")
    event_dir.mkdir(parents=True, exist_ok=True)
    
    # Get today's date for the 'date' field with Europe/Berlin timezone
    berlin_tz = ZoneInfo("Europe/Berlin")
    today = datetime.now(berlin_tz).isoformat(timespec='seconds')
    
    # Parse event date and times with Europe/Berlin timezone
    event_start_dt = datetime.strptime(f"{event_date} {event_start_time}", "%Y-%m-%d %H:%M")
    event_start_str = event_start_dt.replace(tzinfo=berlin_tz).isoformat(timespec='seconds')
    
    event_end_dt = datetime.strptime(f"{event_date} {event_end_time}", "%Y-%m-%d %H:%M")
    event_end_str = event_end_dt.replace(tzinfo=berlin_tz).isoformat(timespec='seconds')
    
    # Format event types for YAML
    event_types_yaml = "\n".join([f"  - {t}" for t in event_types])
    
    # Prepare closed notice
    closed_notice = CLOSED_NOTICE if is_closed else ""
    
    # Format event date for description
    event_date_formatted = format_event_date(event_date)
    
    # Format hosts for YAML and text
    event_hosts_yaml = format_hosts_for_yaml(event_hosts)
    event_hosts_text = format_hosts_for_text(event_hosts)
    
    # Create content from template
    content = EVENT_TEMPLATE.format(
        title=event_title,
        date=today,
        event_start=event_start_str,
        event_end=event_end_str,
        event_date_formatted=event_date_formatted,
        event_time=event_start_time,
        event_hosts=event_hosts_yaml,
        event_hosts_text=event_hosts_text,
        event_types=event_types_yaml,
        closed_notice=closed_notice
    )
    
    # Write content to file
    index_file = event_dir / "_index.md"
    with open(index_file, 'w') as f:
        f.write(content)
    
    print(f"Created: {index_file}")
    
    # Handle cover image if provided
    if cover_image_path:
        # Expand ~ to home directory
        cover_image_path = os.path.expanduser(cover_image_path)
        
        if os.path.exists(cover_image_path):
            cover_dest = event_dir / "cover.png"
            
            # Copy and resize image
            print("\nCopying cover image...")
            run_command(f"cp {cover_image_path} {cover_dest}")
            
            print("Resizing cover image to 512x512...")
            result = run_command(
                f"convert -resize 512x512 {cover_dest} {cover_dest}",
                check=False
            )
            
            if result.returncode != 0:
                print("Warning: Could not resize image. Make sure ImageMagick is installed.")
                print("You can manually resize it later with:")
                print(f"  convert -resize 512x512 {cover_dest} {cover_dest}")
            else:
                print(f"Cover image added: {cover_dest}")
        else:
            print(f"Warning: Image file not found: {cover_image_path}")
    
    # Commit with jj
    print("\nCommitting changes with jj...")
    result = run_command(
        f'jj commit -m "Add event {event_name}"',
        cwd=repo_root
    )
    
    if result.returncode != 0:
        print(f"Error committing: {result.stderr}")
        print("\nFiles created but not committed. You can commit manually with:")
        print(f"  jj commit -m 'Add event {event_name}'")
    else:
        print("Committed successfully!")
    
    # Summary
    print("\n=== Event Created Successfully! ===")
    print(f"\nEvent directory: {event_dir}")
    print(f"Event file: {index_file}")
    
    print("\n=== Next Steps ===")
    print(f"1. Edit the event file: {index_file}")
    if not cover_image_path:
        print(f"2. Add a cover image: {event_dir}/cover.png")
        print(f"   Then resize it: convert -resize 512x512 {event_dir}/cover.png {event_dir}/cover.png")
    print("3. Amend the commit: jj commit --amend")
    print("4. Preview with: cd website && hugo server -D")
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
