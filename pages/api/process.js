import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import os from 'os';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    console.log('🔄 Next.js API: Processing request started');

    // Parse form data
    const form = formidable({
      uploadDir: os.tmpdir(),
      keepExtensions: true,
      maxFileSize: 50 * 1024 * 1024, // 50MB
      allowEmptyFiles: true, // Allow empty files for recording
    });

    const [fields, files] = await new Promise((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        else resolve([fields, files]);
      });
    });

    // Extract files and user query
    const imageFile = files.image?.[0];
    const audioFile = files.audio?.[0];
    const userQuery = fields.userQuery?.[0] || '';

    console.log('📋 Next.js API: Files received');
    console.log(`🔧 Next.js API: Image file: ${imageFile?.originalFilename || 'None'}`);
    console.log(`🔧 Next.js API: Audio file: ${audioFile?.originalFilename || 'None'}`);
    if (userQuery) {
      console.log(`📝 Next.js API: User query: ${userQuery}`);
    }

    // Check if at least one file is provided
    if (!imageFile && !audioFile) {
      return res.status(400).json({ error: 'At least one image or audio file is required' });
    }

    // Create shared directory for Flask
    const sharedDir = path.join(os.tmpdir(), 'flask-gemma');
    if (!fs.existsSync(sharedDir)) {
      fs.mkdirSync(sharedDir, { recursive: true });
    }

    // Prepare request body for Flask
    const requestBody = {
      user_query: userQuery
    };

    // Copy files to shared directory and add to request
    if (imageFile) {
      const imagePath = path.join(sharedDir, `image_${Date.now()}.${path.extname(imageFile.originalFilename)}`);
      fs.copyFileSync(imageFile.filepath, imagePath);
      requestBody.image_path = imagePath;
      console.log(`📁 Next.js API: Image copied to: ${imagePath}`);
    }

    if (audioFile) {
      const audioPath = path.join(sharedDir, `audio_${Date.now()}.${path.extname(audioFile.originalFilename)}`);
      fs.copyFileSync(audioFile.filepath, audioPath);
      requestBody.audio_path = audioPath;
      console.log(`📁 Next.js API: Audio copied to: ${audioPath}`);
    }

    // Send to Flask backend
    try {
      const flaskResponse = await fetch('http://127.0.0.1:5001/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!flaskResponse.ok) {
        const errorText = await flaskResponse.text();
        console.error(`❌ Next.js API: Flask error: ${flaskResponse.status} - ${errorText}`);
        return res.status(500).json({ error: 'Backend processing failed' });
      }

      const flaskData = await flaskResponse.json();
      console.log('✅ Next.js API: Flask processing completed successfully');

      // Clean up temporary files
      try {
        if (imageFile) fs.unlinkSync(imageFile.filepath);
        if (audioFile) fs.unlinkSync(audioFile.filepath);
        console.log('🗑️ Next.js API: Temporary files cleaned up');
      } catch (cleanupError) {
        console.warn('⚠️ Next.js API: Cleanup warning:', cleanupError);
      }

      console.log('✅ Next.js API: Request completed successfully');
      return res.status(200).json(flaskData);
      
    } catch (fetchError) {
      console.error('❌ Next.js API: Connection error to Flask backend:', fetchError);
      
      // Clean up temporary files even on error
      try {
        if (imageFile) fs.unlinkSync(imageFile.filepath);
        if (audioFile) fs.unlinkSync(audioFile.filepath);
        console.log('🗑️ Next.js API: Temporary files cleaned up after error');
      } catch (cleanupError) {
        console.warn('⚠️ Next.js API: Cleanup warning:', cleanupError);
      }
      
      return res.status(503).json({ 
        error: 'Backend service is currently unavailable. Please try again later.',
        details: 'The AI processing service is not responding. This could be due to the backend not being started or network issues.'
      });
    }

  } catch (error) {
    console.error('❌ Next.js API: Error processing request:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
} 