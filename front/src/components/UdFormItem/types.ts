interface TransferItem {
  label: string;
  value: string | number;
  isDel?: boolean;
}

interface ModelValue {
  add?: TransferItem[];
  del?: TransferItem[];
}
