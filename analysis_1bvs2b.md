(base) ashwathkarunakaram@Mac StrokeSentry % python test_model_comparison.py  
🧪 Model Comparison Test: 2B vs 1B
============================================================
🚀 Initializing Model Comparison Test on cpu

📥 Loading Models...
------------------------------
🚀 Loading Gemma 3n 2B model...
📁 Using locally cached 2B model: /Users/ashwathkarunakaram/.cache/kagglehub/models/google/gemma-3n/transformers/gemma-3n-e2b-it/2
🔧 Loading processor and 2B model...
Loading checkpoint shards: 100%|█████████████████████████████████████████████████████████████████████| 3/3 [00:13<00:00,  4.37s/it]
✅ 2B model loaded successfully
⏱️ 2B load time: 15.47s
🚀 Loading Gemma 3 1B IT model...
📥 Loading google/gemma-3-1b-it...
✅ 1B model loaded successfully
⏱️ 1B load time: 5.85s

📁 Testing with files:
   Image: test2.png
   Image: test3.jpeg
   Image: test4.jpeg
   Audio: test2.wav

============================================================

🖼️ TEST 1: Image Analysis Comparison
----------------------------------------

📸 Testing: test2.png
--------------------
🖼️ 2B analyzing image: test2.png
✅ 2B: 78.35s
   Analysis: ## Analysis of the Image: Vegetative Reproduction in Plants

This image presents a detailed explanat...
🖼️ 1B analyzing image: test2.png
✅ 1B: 30.38s
   Analysis: The image appears to be a digital illustration. It's a highly detailed, somewhat stylized representa...

📸 Testing: test3.jpeg
--------------------
🖼️ 2B analyzing image: test3.jpeg
✅ 2B: 70.01s
   Analysis: ## Analysis of the Image: Derivative of a Function

**1. What the image shows:**

The image displays...
🖼️ 1B analyzing image: test3.jpeg
✅ 1B: 29.72s
   Analysis: This image is a high-resolution, panoramic photograph of a vast, sprawling landscape. It’s predomina...

📸 Testing: test4.jpeg
--------------------
🖼️ 2B analyzing image: test4.jpeg
✅ 2B: 68.94s
   Analysis: ## Analysis of the Image: "What is (a+b)²?"

**1. What the image shows:**

The image shows a handwri...
🖼️ 1B analyzing image: test4.jpeg
✅ 1B: 30.02s
   Analysis: The image is a high-resolution photograph of a complex geometric structure. It appears to be a styli...

============================================================

🎵 TEST 2: Audio Analysis Comparison
----------------------------------------

🎤 Testing: test2.wav
--------------------
🎵 2B analyzing audio: test2.wav
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
        - Avoid using `tokenizers` before the fork if possible
        - Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
✅ 2B: 22.85s
   Analysis: The user is saying "Hello, my name is Ashut."

This is a greeting and introduction. It is a statemen...
🎵 1B analyzing audio: test2.wav
✅ 1B: 32.63s
   Analysis: The audio contains a series of short, fragmented sequences of sounds.  It seems to be a vocal sample...

============================================================

📊 SUMMARY REPORT
----------------------------------------

🖼️ Image Analysis Times:

   test2.png:
     2B: 78.35s
     1B: 30.38s

   test3.jpeg:
     2B: 70.01s
     1B: 29.72s

   test4.jpeg:
     2B: 68.94s
     1B: 30.02s

🎵 Audio Analysis Times:

   test2.wav:
     2B: 22.85s
     1B: 32.63s

📈 2B Average Image Time: 72.43s
📈 1B Average Image Time: 30.04s
📈 2B Average Audio Time: 22.85s
📈 1B Average Audio Time: 32.63s

⚡ 1B is 2.4x faster than 2B for images
⚡ 1B is 0.7x slower than 2B for audio

============================================================
✅ Comparison test completed!