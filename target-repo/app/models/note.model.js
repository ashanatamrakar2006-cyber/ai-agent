const mongoose = require('mongoose');

const NoteSchema = mongoose.Schema({
    title: String,
    content: String,
    tags: [String]
}, {
    timestamps: true
});

NoteSchema.index({ content: 'text' });

module.exports = mongoose.model('Note', NoteSchema);