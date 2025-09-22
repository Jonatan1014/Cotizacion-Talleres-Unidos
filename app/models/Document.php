<?php
class Document {
    public $id;
    public $original_name;
    public $file_path;
    public $file_type;
    public $file_size;
    public $status;
    public $processed_path;
    public $created_at;
    public $updated_at;

    public function __construct($data = []) {
        foreach ($data as $key => $value) {
            if (property_exists($this, $key)) {
                $this->$key = $value;
            }
        }
    }

    public function toArray() {
        return [
            'id' => $this->id,
            'original_name' => $this->original_name,
            'file_path' => $this->file_path,
            'file_type' => $this->file_type,
            'file_size' => $this->file_size,
            'status' => $this->status,
            'processed_path' => $this->processed_path,
            'created_at' => $this->created_at,
            'updated_at' => $this->updated_at
        ];
    }
}
?>