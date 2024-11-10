import React from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import GradientBackground from '../GradientBackground.tsx';
import { Box, Button, Typography } from '@mui/material';
import DynamicBarChart from '../DynamicBarChart.tsx';
import logo from '../logos/logo_completo.png';

// Styling constants
const containerStyles = {
  textAlign: 'center',
  position: 'relative',
  height: '100vh',
  overflow: 'hidden',
};

const logoContainerStyles = {
  backgroundColor: 'white',
  padding: 0.2,
  borderRadius: '18px',
  display: 'flex',
  alignItems: 'center',
};

// Function for file upload
const uploadFile = async (file: File, userId: string) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`http://localhost:8000/upload-csv/${userId}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(await response.json());
  return response.json();
};

const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const userId = uuidv4();

    try {
      await uploadFile(file, userId);
      navigate(`/chatbot/${userId}`);
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  return (
    <Box sx={containerStyles}>
      <GradientBackground />
      <Box sx={{ paddingTop: 10, position: 'relative', zIndex: 1 }}>
        <Typography variant="h4" color="white" gutterBottom>
          Analyze and modify your data effortlessly with our smart data assistant.
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 5 }}>
          <Box sx={logoContainerStyles}>
            <img src={logo} alt="Logo" style={{ width: 325 }} />
          </Box>
        </Box>

        <Box sx={{ marginTop: 6 }}>
          <Button variant="contained" component="label" size="large">
            Upload CSV File
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={handleFileUpload}
            />
          </Button>
        </Box>
      </Box>
      <DynamicBarChart />
    </Box>
  );
};

export default Home;
