# 🫶 Frontend Setup

This is an [Expo](https://expo.dev) project, meaning it can run on Web, iOS, and Android! Expo uses [React Native](https://reactnative.dev/).

In the `frontend` folder:

### 1. Install dependencies

```bash
npm i
```

### 2. Start the app

```bash
npx expo start
```

You can now view the app on your laptop at [localhost:8081](http://localhost:8081), or scan the QR code in the terminal to preview the app on your phone!

(Note: you need to have the Expo app installed to run on your phone)

## 💅 Development

### Styling

This project uses [Nativewind](https://www.nativewind.dev/) (mobile Tailwind CSS) for styling :)

Sometimes third-party libraries or native UI components (like the camera) don't support Nativewind. In that case, we must revert to vanilla styling 😔

### Icons

When adding an icon to the project, you need to find an iOS variant ([SF Symbols](https://developer.apple.com/sf-symbols)) and a Web/Android variant ([Material Icons](https://icons.expo.fyi)). Then add the mapping to `frontend/components/ui/icon-symbol.tsx`:

```typescript
const MAPPING = {
  "house.fill": "home",
  ...
} as IconMapping;
```

### API Integration Testing

Start both the frontend and the backend!

If you're testing the frontend on your laptop, you're all good to go. But if you want to demo the app on your phone, you have to use `ngrok`:

1. Install `ngrok` (`brew install ngrok`)

2. Make an account and authenticate in your terminal by following [these instructions](https://dashboard.ngrok.com/get-started/your-authtoken)

3. Run `ngrok http 8000` in your terminal. This generates a (temporary) public url for our backend server, which can be reached by any device :D

4. Replace the url in `constants/api.ts` with the new `ngrok` link and you're good to go! 🎉
