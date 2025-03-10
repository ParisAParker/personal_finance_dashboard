const handler = Plaid.create({
    token: "your-link-token",
    onSuccess: (public_token, metadata) => {
      console.log("Public Token: ", public_token);
      // Send this public_token to your backend
    },
  });
  
  handler.open();
  