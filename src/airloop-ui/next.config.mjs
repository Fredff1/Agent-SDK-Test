/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,
  output: "export",
  async rewrites() {
    return [
      {
        source: "/api/chat",
        destination: "http://127.0.0.1:8000/api/chat",
      },
      {
        source: "/api/feedback",
        destination: "http://127.0.0.1:8000/api/feedback",
      },
    ];
  },
};

export default nextConfig;
