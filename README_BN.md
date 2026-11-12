# AI Food Video Clip Finder (লোকাল ব্রাউজার অ্যাপ)

## কী করে
- MP4/MOV/MKV/WEBM/M4V/AVI ভিডিও আপলোড নেয়
- নির্দিষ্ট বিরতিতে ভিডিও থেকে ছবি নেয়
- OpenAI vision model দিয়ে খাবার, পরিবেশন, টেস্টিং ও আকর্ষণীয় দৃশ্য শনাক্ত করার চেষ্টা করে
- প্রতিটি হাইলাইটের টাইমস্ট্যাম্প দেয়
- FFmpeg দিয়ে নির্বাচিত অংশ MP4 ক্লিপ হিসেবে তৈরি করে ডাউনলোড দেয়

## প্রয়োজন
- Windows 10/11, macOS বা Linux কম্পিউটার
- Python 3.10+
- FFmpeg ও FFprobe ইনস্টল করে PATH-এ যোগ করা
- OpenAI API key এবং API billing/credits

## Windows-এ চালানো
1. Python ইনস্টল করুন: https://www.python.org/downloads/
2. FFmpeg ইনস্টল করুন: https://ffmpeg.org/download.html
3. ZIP extract করুন।
4. ওই ফোল্ডারে Command Prompt খুলুন।
5. চালান:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

6. ব্রাউজারে খুলুন: http://127.0.0.1:8000

## macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```
তারপর http://127.0.0.1:8000 খুলুন।

## গুরুত্বপূর্ণ
- এটি নিজের কম্পিউটারে চলবে; কোনো পাবলিক ওয়েবসাইটে আপলোড করা হয়নি।
- ভিডিওর ছবি OpenAI API-তে বিশ্লেষণের জন্য পাঠানো হয়। API ব্যবহারে খরচ হতে পারে।
- ডিফল্টভাবে প্রতি ৪ সেকেন্ডে একটি ফ্রেম বিশ্লেষণ করা হয়। ছোট/দ্রুত দৃশ্য বাদ পড়তে পারে।
- বেশি নির্ভুলতার জন্য `FRAME_INTERVAL_SECONDS=2` সেট করা যায়, তবে খরচ ও সময় বাড়বে।
- বড় ভিডিওর জন্য `MAX_UPLOAD_BYTES` পরিবেশ ভেরিয়েবল দিয়ে আপলোড সীমা বাড়ানো যায়।
- শুধু নিজের বা ব্যবহারের অনুমতি থাকা ভিডিও নিয়ে কাজ করুন।
- এটি একটি প্রাথমিক MVP; AI-এর টাইমস্ট্যাম্প সবসময় যাচাই করে নেবেন।
