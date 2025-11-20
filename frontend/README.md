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

This project uses [Nativewind](https://www.nativewind.dev/) (mobile Tailwind CSS) for styling :)

When adding an icon to the project, you need to find an iOS variant ([SF Symbols](https://developer.apple.com/sf-symbols)) and a Web/Android variant ([Material Icons](https://icons.expo.fyi)). Then add the mapping to `frontend/components/ui/icon-symbol.tsx`.