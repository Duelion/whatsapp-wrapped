# Test Data Directory

## ⚠️ IMPORTANT - Privacy Notice

This directory is for **local test data only**. 

**DO NOT commit WhatsApp chat files to git!**

## Setup

To run tests, place your own WhatsApp chat export file here:

1. Export a WhatsApp chat (`.zip` or `.txt` format)
2. Place it in this directory: `tests/data/`
3. Run tests with: `uv run pytest`

## Files

- Only keep **one** chat file (`.zip` or `.txt`) in this directory
- All `.zip` and `.txt` files are gitignored for privacy
- Tests will automatically find and use the chat file

## Why No Test Data in Git?

WhatsApp chat exports contain:
- Private conversations
- Personal information
- Contact details
- Media references

These should **never** be committed to a public repository.







