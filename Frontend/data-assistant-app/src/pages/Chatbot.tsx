import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Avatar,
  CircularProgress
} from '@mui/material';
import GradientBackground from '../GradientBackground.tsx';
import logo from '../logos/logo.png';
import complete_logo from '../logos/logo_completo.png';
import '@fontsource/montserrat';

// Styling constants
const containerStyles = {
  position: 'relative',
  minHeight: '100vh',
  overflow: 'hidden',
};

const logoContainerStyles = {
  backgroundColor: 'white', // Corrected background color property
  padding: '5px 20px', // Adds padding to center the content inside the white box
  borderRadius: '18px',
  display: 'flex',
  alignItems: 'center', // Centers content vertically
  justifyContent: 'center', // Centers content horizontally
  boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.2)', // Adds shadow for a subtle effect

};

const Chatbot: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();

  // Redirect to home if userId is missing
  useEffect(() => {
    if (!userId) {
      navigate('/');
    }
  }, [userId, navigate]);

  const [messages, setMessages] = useState<{ sender: string; text: string | JSX.Element }[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [dataImageUrl, setDataImageUrl] = useState<string | null>(null);
  const [csvDownloaded, setCsvDownloaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Parse text with bold formatting
  const parseTextFormat = (text: string): JSX.Element => (
    <span>
      {text.split('\n\n').map((paragraph, index) => (
        <span key={index}>
          {paragraph.split('\n').map((line, i) => (
            <React.Fragment key={i}>
              {line.split(/(\*\*.*?\*\*)/).map((segment, j) =>
                segment.startsWith("**") && segment.endsWith("**")
                  ? <strong key={j}>{segment.slice(2, -2)}</strong>
                  : segment
              )}
              <br />
            </React.Fragment>
          ))}
        </span>
      ))}
    </span>
  );

  // Fetches an image of the data head
  const fetchDataHeadImage = async () => {
    try {
      const response = await fetch(`http://localhost:8000/data-head-image/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch data head image');
      setDataImageUrl(URL.createObjectURL(await response.blob()));
    } catch (error) {
      console.error('Error fetching data head image:', error);
    }
  };

  useEffect(() => {
    if (userId) fetchDataHeadImage();
  }, [userId]);

  // Sends a message to the backend
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    setMessages((prev) => [...prev, { sender: 'user', text: inputValue }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8000/chat/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: inputValue }),
      });

      if (!response.ok) throw new Error('Error communicating with the backend');

      if (response.headers.get('content-type')?.includes('image/png')) {
        const imageUrl = URL.createObjectURL(await response.blob());
        setMessages((prev) => [
          ...prev,
          { sender: 'bot', text: <Box component="img" src={imageUrl} alt="Chart" sx={{ width: '100%', maxWidth: 400, height: 'auto', borderRadius: 2 }} /> },
        ]);
      } else {
        const data = await response.json();
        setMessages((prev) => [...prev, { sender: 'bot', text: parseTextFormat(data.response) }]);
      }

      await fetchDataHeadImage();
      setCsvDownloaded(true);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Error: Unable to get response from the server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to download ${filename}`);
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error(`Error downloading ${filename}:`, error);
    }
  };

  const handleDownloadCharts = () => handleDownload(`http://localhost:8000/download-charts/${userId}`, `${userId}_charts.zip`);
  const handleDownloadCsv = () => handleDownload(`http://localhost:8000/download-csv/${userId}`, 'modified_data.csv');

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Box sx={containerStyles}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: -1 }}>
        <GradientBackground />
      </Box>

      <Box sx={{ paddingTop: 5, position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minHeight: '100vh' }}>
        <Typography variant="h5" color="white" gutterBottom>
          {userId ? `Session ID: ${userId}` : 'No user session'}
        </Typography>

        {dataImageUrl && (
          <Box component="img" src={dataImageUrl} alt="Data Head" sx={{ width: '100%', maxWidth: 500, height: 'auto', borderRadius: 2, boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)', marginBottom: 4 }} />
        )}

        <Box sx={{ textAlign: 'center', marginBottom: 4 }}>
          <Box sx={logoContainerStyles}>
            <img src={complete_logo} alt="Logo" style={{ width: 270 }} />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, marginTop: 4 }}>
            <Button variant="contained" color="primary" onClick={handleDownloadCharts}>Download Charts</Button>
            <Button variant="contained" color="secondary" onClick={handleDownloadCsv} disabled={!csvDownloaded}>Download CSV</Button>
          </Box>
        </Box>

        <Box sx={{ width: '75%', maxHeight: '80vh', overflowY: 'auto', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 2, padding: 2 }}>
          {messages.map((message, index) => (
            <Box key={index} sx={{ display: 'flex', justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start', marginBottom: 2 }}>
              <Paper sx={{ padding: 2, maxWidth: '60%', backgroundColor: message.sender === 'user' ? '#e0f7fa' : '#f1f1f1', borderRadius: '20px' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {message.sender === 'bot' && (
                    <Box component="img" src={logo} alt="Logo" sx={{ marginRight: 2, width: 60, height: 60, borderRadius: '50%', objectFit: 'contain' }} />
                  )}
                  <Typography component="div">{message.text}</Typography>
                  {message.sender === 'user' && (
                    <Avatar sx={{ marginLeft: 2, backgroundColor: '#2196f3', width: 40, height: 40 }}>U</Avatar>
                  )}
                </Box>
              </Paper>
            </Box>
          ))}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, width: '80%', backgroundColor: 'rgba(255, 255, 255, 0.2)', padding: 2, borderRadius: 2, marginBottom: 4 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Enter your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => { if (e.key === 'Enter' && !isLoading) handleSendMessage(); }}
            sx={{ backgroundColor: 'white', borderRadius: 1 }}
            disabled={isLoading}
          />
          <Button variant="contained" onClick={handleSendMessage} disabled={isLoading}>
            {isLoading ? <CircularProgress size={24} /> : 'Send'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default Chatbot;
