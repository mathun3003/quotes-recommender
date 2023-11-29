import { TextField, Button, styled, Box } from '@mui/material';

export const SearchButton = styled(Button)({
  backgroundColor: '#183D3D',
  color: 'white',
  borderRadius: '30px',
  textTransform: 'none',
  fontWeight: 500,

  '&:hover': {
    backgroundColor: '#183D3D',
    borderRadius: '30px',
  },
});

export const SearchField = styled(TextField)({
  width: '700px',
  '& .MuiInputBase-root': {
    padding: '2px',
    fontSize: '19px',
    fontWeight: 400,
    lineHeight: '132%',
    letterSpacing: '-0.01em',

    borderRadius: '12px',
    color: 'white',

    border: `1px solid rgba(2, 2, 2, 0.15)`,

    '& ::placeholder': {
      color: '#808191',
    },
  },

  '& fieldset': {
    border: 'none',
  },

  '& .MuiOutlinedInput-root': {
    border: `3px solid rgba(241, 241, 241, 0.15)`,
    borderRadius: '30px',

    fontWeight: 400,
    minHeight: 55,

    '&:hover': {
      border: `3.2px solid rgba(241, 241, 241, 0.35)`,
    },
    '&.Mui-focused': {
      border: `3.3px solid rgba(241, 241, 241, 0.35)`,
    },
  },
});

export const TagsOutfield = styled(Box)({
  '& .MuiChip-root': {
    backgroundColor: '#353535',
  },

  '& .MuiChip-root .MuiChip-label': {
    color: 'white',
  },

  '& .MuiAutocomplete-endAdornment button': {
    color: 'white',
  },
});

export const ScrollStyles = {
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: '#D3D3D3',
    border: '4px solid transparent',
    borderRadius: '8px',
    backgroundClip: 'padding-box',
  },

  '&::-webkit-scrollbar': {
    width: '16px',
  },
};

export const TagsField = styled(TextField)({
  width: '500px',
  '& .MuiInputBase-root': {
    padding: '2px 4px',
    fontSize: '12px',
    fontWeight: 400,
    lineHeight: '132%',
    letterSpacing: '-0.01em',

    maxHeight: '100px',
    overflowY: 'scroll',
    ...ScrollStyles,

    borderRadius: '12px',
    color: 'white',

    border: `1px solid rgba(2, 2, 2, 0.15)`,

    '& ::placeholder': {
      color: '#808191',
    },
  },

  '& fieldset': {
    border: 'none',
  },

  '& .MuiOutlinedInput-root': {
    border: `2px solid rgba(241, 241, 241, 0.15)`,
    // borderRadius: '30px',

    fontWeight: 400,
    minHeight: 55,

    '&:hover': {
      border: `2.2px solid rgba(241, 241, 241, 0.35)`,
    },
    '&.Mui-focused': {
      border: `2.3px solid rgba(241, 241, 241, 0.35)`,
    },
  },
});

export const PaperComponentContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  backgroundColor: '#0f2424',
  borderRadius: '10px',
  padding: '10px',
  zIndex: 1,
  boxShadow:
    '0px 39px 60px -12px rgba(0, 0, 0, 0.08), 0px 0px 14px -4px rgba(0, 0, 0, 0.05), 0px 32px 48px -8px rgba(0, 0, 0, 0.1)',

  '& .MuiAutocomplete-loading': {
    padding: '8px',
  },

  '& ul': {
    overflowY: 'scroll',
    ...ScrollStyles,
    backgroundColor: '#0f2424',
    padding: 0,
    maxHeight: '500px',
  },

  '& li': {
    borderRadius: '8px',
    backgroundColor: '#0f2424',
    color: '#F1F1F5',
    padding: '10px 8px',
    fontFamily: 'Inter',
    fontSize: '14px',
  },

  '& li:hover': {
    color: '#F7F7F7',
    backgroundColor: '#44444F',
  },

  '& .MuiAutocomplete-noOptions': {
    fontSize: '14px',
    fontWeight: 400,
    letterSpacing: '-0.01em',
    lineHeight: '130%',
  },
}));
