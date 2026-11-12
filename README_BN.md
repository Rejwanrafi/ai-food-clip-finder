# Android ব্রাউজার ভার্সন — AI Food Clip Finder

## গুরুত্বপূর্ণ
এই ZIP একটি deploy করার মতো ওয়েব অ্যাপ। Android Chrome-এ ব্যবহার করতে হলে এটি ইন্টারনেটে একটি সার্ভারে deploy/host করতে হবে। শুধু ZIP ফোনে extract করলে অ্যাপ চলবে না। বড় ভিডিও বিশ্লেষণের কাজ সার্ভারে হবে; ফোন শুধু আপলোড ও ক্লিপ ডাউনলোড করবে।

## সহজ deploy (Docker সমর্থিত hosting)
1. ZIP extract করে GitHub repository-তে project files upload করুন।
2. Docker সমর্থিত hosting provider-এ নতুন Web Service তৈরি করে repository connect করুন।
3. `OPENAI_API_KEY` নামে secret environment variable যোগ করুন।
4. সার্ভারে FFmpeg ইনস্টল থাকা নিশ্চিত করুন (Dockerfile-এ আছে)।
5. সার্ভারের persistent disk/storage ব্যবহার করুন; বড় ভিডিওর জন্য যথেষ্ট disk এবং upload/body limit নিশ্চিত করুন।
6. Deploy হলে পাওয়া HTTPS URL Android Chrome-এ খুলুন।

## API key
সার্ভারে `OPENAI_API_KEY` secret হিসেবে সেট করাই নিরাপদ। সেক্ষেত্রে ব্যবহারকারীর UI-তে key field ফাঁকা রাখা যাবে। API usage charge হবে। API key কখনো public GitHub repository-তে লিখবেন না।

## সীমাবদ্ধতা ও গোপনীয়তা
- এটি একটি প্রাথমিক MVP, পূর্ণাঙ্গ বাণিজ্যিক সার্ভিস নয়।
- ভিডিওর নির্দিষ্ট বিরতিতে ফ্রেম নিয়ে AI-কে পাঠানো হয়; অল্প সময়ের দৃশ্য বাদ পড়তে পারে। `FRAME_INTERVAL_SECONDS=2` করলে বেশি ফ্রেম দেখা হবে, কিন্তু খরচ/সময় বাড়বে।
- বড় ফাইল গ্রহণ করা hosting provider, reverse proxy, storage ও সার্ভারের সীমার ওপর নির্ভর করে। Render-এর মতো সাধারণ web hosting-এ বড় ভিডিওর আপলোড সীমা/সময় আগে যাচাই করুন।
- আপলোড করা ভিডিও সার্ভারে `data/` ফোল্ডারে থাকে। এটি public internet-এ উন্মুক্ত করবেন না; authentication, storage quota, cleanup ও private access যোগ করা উচিত।
- কেবল নিজের বা অনুমতিপ্রাপ্ত ভিডিও ব্যবহার করুন। ক্লিপ ডাউনলোড করলেই পুনঃপ্রকাশের অধিকার পাওয়া যায় না।
