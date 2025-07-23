import axios from 'axios';

export const api = axios.create({
  baseURL: "",
  timeout: 120_000,
});

/* export const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
}); */