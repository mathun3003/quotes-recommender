import { styled, Box, Typography } from '@mui/material';

export const ResultsContainer = styled(Box)({
  margin: '32px',
  borderRadius: '34px',
  background:
    'linear-gradient(90deg, #092626 0.24%, rgba(46, 44, 44, 0.66) 49.62%, rgba(94, 91, 95, 0.28) 105.83%, rgba(0, 0, 0, 0.11) 146.1%)',
  padding: '10px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',

  height: '600px',
  maxHeight: '600px',
});

export const Header = styled(Typography)({
  flexGrow: 1,
  color: 'white',
  padding: '16px',
  fontWeight: 400,
  fontSize: '30px',
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

export const BubbleContainer = styled(Box)({
  width: '100%',

  overflowY: 'scroll',
  ...ScrollStyles,
});

export const ChatBubbleContainer = styled('div')(({ position }) => ({
  display: 'flex',
  padding: '4px 100px',
  //   justifyContent: 'flex-end',
  justifyContent: position === 'left' ? 'flex-start' : 'flex-end',
  marginBottom: '10px',
}));

export const Bubble = styled('div')(({ position }) => ({
  '--r': '25px',
  '--t': '30px',
  maxWidth: '700px',
  padding: 'calc(2 * var(--r) / 3)',
  WebkitMask: `
      radial-gradient(var(--t) at var(--_d) 0, #0000 98%, #000 102%)
        var(--_d) 100% / calc(100% - var(--r)) var(--t) no-repeat,
      conic-gradient(at var(--r) var(--r), #000 75%, #0000 0)
        calc(var(--r) / -2) calc(var(--r) / -2) padding-box,
      radial-gradient(50% 50%, #000 98%, #0000 101%)
        0 0 / var(--r) var(--r) space padding-box;
    `,
  background: 'linear-gradient(135deg, #FE6D00, #1384C5) border-box',
  color: '#fff',
  ...(position === 'left'
    ? {
        '--_d': '0%',
        borderLeft: `${'var(--t) solid #0000'}`,
        marginRight: 'var(--t)',
        placeSelf: 'start',
      }
    : {
        '--_d': '100%',
        borderRight: `${'var(--t) solid #0000'}`,
        marginLeft: 'var(--t)',
        placeSelf: 'end',
      }),
}));
